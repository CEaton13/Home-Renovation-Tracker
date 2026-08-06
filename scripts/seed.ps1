# scripts/seed.ps1
# Clears all existing projects/tasks and seeds three demo projects at
# different lifecycle stages: completed (est vs actual variance),
# in-progress (mixed task states), and early planning (all todo).

$base = "http://127.0.0.1:5000"

Write-Host "Clearing existing data..."
$projects = (Invoke-RestMethod -Uri "$base/projects" -Method Get).projects
foreach ($p in $projects) {
    $tasks = (Invoke-RestMethod -Uri "$base/projects/$($p.id)/tasks" -Method Get).tasks
    foreach ($t in $tasks) {
        Invoke-RestMethod -Uri "$base/tasks/$($t.id)?confirm=true" -Method Delete | Out-Null
    }
    Invoke-RestMethod -Uri "$base/projects/$($p.id)?confirm=true" -Method Delete | Out-Null
}
Write-Host "Cleared $($projects.Count) project(s)."

function New-Project($name, $room, $budgetDollars, $start, $target) {
    $body = @{
        name = $name; room = $room
        budget = [math]::Round($budgetDollars * 100)
        start_date = $start; target_completion_date = $target
    } | ConvertTo-Json
    Write-Host "Creating '$name' (waiting on AI enrichment, ~10s)..."
    return Invoke-RestMethod -Uri "$base/projects" -Method Post -Body $body -ContentType "application/json"
}

function New-Task($projectId, $description, $trade, $estDollars) {
    $body = @{
        description = $description; trade_category = $trade
        est_cost = [math]::Round($estDollars * 100)
    } | ConvertTo-Json
    return Invoke-RestMethod -Uri "$base/projects/$projectId/tasks" -Method Post -Body $body -ContentType "application/json"
}

function Complete-Task($taskId, $actualDollars) {
    $body = @{ actual_cost = [math]::Round($actualDollars * 100) } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/tasks/$taskId/complete" -Method Post -Body $body -ContentType "application/json" | Out-Null
}

# --- Project 1: Completed. Every task done, showing real est-vs-actual variance. ---
$p1 = New-Project "Guest Bathroom Remodel" "Guest Bathroom" 4500 "2026-05-01" "2026-06-15"
$t = New-Task $p1.id "Replace vanity and sink" "carpentry" 1200
Complete-Task $t.id 1350   # ran over
$t = New-Task $p1.id "Replace toilet" "plumbing" 350
Complete-Task $t.id 320    # came in under
$t = New-Task $p1.id "Retile shower floor" "flooring" 900
Complete-Task $t.id 900    # exact
$t = New-Task $p1.id "Repaint walls and ceiling" "painting" 250
Complete-Task $t.id 275
$t = New-Task $p1.id "Upgrade vanity lighting" "electrical" 400
Complete-Task $t.id 410
Invoke-RestMethod -Uri "$base/projects/$($p1.id)" -Method Put -Body (@{ project_status = "completed" } | ConvertTo-Json) -ContentType "application/json" | Out-Null
Write-Host "  -> completed"

# --- Project 2: In progress. Mix of done, in_progress, and todo. ---
$p2 = New-Project "Basement Finishing" "Basement" 18000 "2026-07-01" "2026-10-01"
$t = New-Task $p2.id "Frame new walls for media room" "carpentry" 3200
Complete-Task $t.id 3400
$t = New-Task $p2.id "Run electrical for outlets and lighting" "electrical" 2500
Complete-Task $t.id 2450
$t = New-Task $p2.id "Install drywall" "carpentry" 2800
Invoke-RestMethod -Uri "$base/tasks/$($t.id)" -Method Put -Body (@{ task_status = "in_progress" } | ConvertTo-Json) -ContentType "application/json" | Out-Null
New-Task $p2.id "Install carpet flooring" "flooring" 2200 | Out-Null
New-Task $p2.id "Paint finished walls" "painting" 900 | Out-Null
Write-Host "  -> in_progress, tasks mixed"

# --- Project 3: Early planning. Everything still todo. ---
$p3 = New-Project "Backyard Deck Rebuild" "Backyard" 9000 "2026-09-15" "2026-11-01"
New-Task $p3.id "Demo existing deck" "general" 800 | Out-Null
New-Task $p3.id "Pour new footings" "general" 1500 | Out-Null
New-Task $p3.id "Frame deck structure" "carpentry" 3200 | Out-Null
New-Task $p3.id "Install decking boards and railing" "carpentry" 2800 | Out-Null
New-Task $p3.id "Stain and seal" "painting" 500 | Out-Null
Write-Host "  -> planning, all tasks todo"

Write-Host "`nSeeding complete: 3 projects created."