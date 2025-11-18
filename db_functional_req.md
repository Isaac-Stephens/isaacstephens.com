|   | Description                                            | Owner                          | Staff                       | Trainer                           | Member      |
|---|--------------------------------------------------------|--------------------------------|-----------------------------|-----------------------------------|-------------|
| A | Add a new Member                                       | Manage Memberships             | Manage Memberships          |                                   |             |
| B | Update Member Information                              | Manage Memberships             | Manage Memberships          |                                   |             |
| C | Delete a Member                                        | Manage Memberships             |                             |                                   |             |
| D | Add a Payment for a Member                             | Manage Payments                | Manage Payments             |                                   | My Payments |
| E | Regeister Staff/Trainer                                | Manage Staff / Manage Trainers |                             |                                   |             |
| F | Assign Trainer to a Member                             | Manage Trainers                | Manage Memberships          | My Clients                        |             |
| G | Log an Exercise for a member                           | Exercise Logs                  |                             | Exercise Logs / Workout Plans     | My Workouts |
| H | Modify an exercise record                              | Exercise Logs                  |                             | Exercise Logs / Workout Plans     | My Workouts |
| I | Delete an exercise                                     | Exercise Logs                  |                             | Exercise Logs / Workout Plans     | My Workouts |
| J | Get exercises for a specific member (Exercise History) | Exercise Logs                  |                             | Exercise Logs / My Clients        | My Workouts |
| K | List Clients for a Trainer                             | Manage Trainers                | Manage Memberships          | My Clients                        |             |
| L | Aggregation: Total Payments/Revenue                    | Manage Payments / Dashboard    | Manage Payments / Dashboard |                                   | My Payments |
| M | Aggregation: Average RPE                               | Exercise Logs                  |                             | Exercise Logs / Progress Reports  | My Workouts |
| N | Aggregation: Max Weight Lifted By a Member             | Exercise Logs                  |                             | Exercise Logs / Progress Reports  | My Workouts |
| O | Aggregation: Average Run Distance                      | Exercise Logs                  |                             | Exercise Logs / Progress Reports  | My Workouts |
| P | Reports and UI Behavior                                |                                |                             |                                   |             |
| Q | Error Handling and Visibility                          | Error Logs (ALL)               | Error Logs                  |                                   |             |


# Application Program Design
General notes (common to all functions)
1. Always open a database connection at the start of an operation and close it at the end.
2. For multi-step operations that must all succeed together, use a transaction: start transaction → do steps → on
success commit → on failure rollback.
3. Validate user input before sending to the database (required fields present, numeric ranges, date logic).
4. Use parameterized queries in the application code to avoid SQL injection (implementation detail).
5. Show clear success / error messages to the user when operations complete or fail.



## A. Add a new member (with optional phone numbers and emergency contacts)
1. Ask the user for member info: first name, last name, birth date, membership start date, email, sex.
2. Validate fields:
   - first/last name present
   - email format valid
   - birth date is before today
   - membership start date is not before birth date
3. Open DB connection and begin a transaction.
4. Insert a new row into Members with the provided fields; get the new member_id assigned by the database.
5. If the user provided phone numbers:
   - For each phone number: insert a row into PhoneNumbers with the new member_id, phone number, and
type.
1. If the user provided emergency contacts:
    - For each contact: insert a row into EmergencyContacts with the new member_id and contact details.
1. Commit the transaction and close the connection.
2. Return success and the new member_id, or return an error if any step fails (rollback).
## B. Update member information
1. Ask the user which member to update (member_id) and which fields to change.
2. Validate the new values (same checks as insert).
3. Open DB connection.
4. Update the Members row for that member_id with the new values.
5. If phone numbers or emergency contacts are also edited:
   - For edits: update the appropriate PhoneNumbers or EmergencyContacts rows.
   - For additions: insert new rows linked to the member_id.
   - For deletions: remove the specified PhoneNumbers or EmergencyContacts rows.
6. Commit (if batched) and close connection.
7. Return success or error.
## C. Delete a member (clean up dependents)
1. Ask the user to confirm deletion and show a warning that associated data will be removed.
2. Open DB connection and begin transaction.
3. Delete the member row from Members.
   - Because EmergencyContacts and Exercises are defined with ON DELETE CASCADE, those rows will
be removed automatically.
   - If PhoneNumbers and Payments do not have cascade, explicitly delete PhoneNumbers and Payments rows
for that member_id before deleting the member.
1. Commit the transaction and close connection.
2. Return success or error.
## D. Add a payment for a member
1. Ask for member_id, amount, and payment date.
2. Validate: member exists, amount > 0, payment date valid.
3. Insert a new Payments row with member_id, amount, payment_date.
4. Return confirmation and updated payment total if requested.
## E. Register staff / trainer
1. Collect staff personal info (ssn, first name, last name, employment date, birth date, address).
2. Validate: ssn uniqueness, birth date before employment date.
3. Insert a Staff row; get staff_id.
4. If this staff is a trainer:
   - Insert a Trainers row referencing staff_id with speciality.
5. If the staff has a pay type (contractor/hourly/salary), insert the appropriate subtype row.
6. Commit and return staff_id.
## F. Assign a trainer to a member (trainer-client)
1. Ask for trainer_id and member_id, start date, optional notes.
2. Validate: trainer_id references an existing Trainer; member exists.
3. Check if a pairing (trainer_id, member_id) already exists:
   - If it exists and is active, inform the user (do not duplicate).
   - If it exists but ended earlier, allow a new record if your design permits or update the existing record’s end date.
4. Insert a TrainerClients row with trainer_id, member_id client_start_date, client_end_date (NULL if ongoing), notes.
5. Return confirmation.
## G. Log an exercise for a member (strength or cardio)
1. Ask for member_id, exercise_name, rpe, exercise_date, and exercise type (strength or cardio).
2. Validate: member exists, rpe between 1 and 10, date valid.
3. Begin transaction.
4. Insert a new Exercises row and capture exercise_id.
5. If type == strength:
   - Ask for exercise_weight, weight_unit, num_sets, num_repetitions, notes.
   - Validate numeric fields > 0 and weight_unit in allowed set.
   - Insert a Strength_Exercises row referencing exercise_id.
6. Else if type == cardio:
     - Ask for avg_hr and time_taken.
     - Validate avg_hr > 0 and time_taken present.
     - Insert a Cardio_Exercises row referencing exercise_id and capture cardio_id.
     - Ask whether the cardio is a Run or Bike ride.
       - If Run: ask distance_unit and distance, optional laps; validate distance > 0; insert Runs row
referencing cardio_id.
       - If Bike: ask distance_unit and distance and wattage; validate; insert Bike_Rides row referencing
cardio_id.
1. Commit transaction and return the new exercise record id(s).
2. If any validation fails or an insert fails, rollback and inform the user.
## H. Modify an exercise record
1. Ask which exercise to modify (exercise_id) and which fields to change.
2. Validate that the exercise exists and the new values are in valid ranges.
3. Update the Exercises row.
4. If the exercise has a strength subtype (exists in Strength_Exercises), update that row accordingly.
5. If the exercise has a cardio subtype, update Cardio_Exercises and its specific Run/Bike row.
6. Commit and return success.
## I. Delete an exercise
1. Confirm deletion with the user.
2. Delete the Exercises row for exercise_id.
   - ON DELETE CASCADE will remove strength/cardio subtype rows; if any subtype tables lack cascade, delete them explicitly first.
3. Return success.
## J. Get exercises for a specific member (user-input query)
1. Ask the user to enter a member_id or search by name and pick a member.
2. Validate the chosen member exists.
3. Steps to gather results:
   - Fetch all Exercises rows for the member ordered by date (newest first).
    - For each exercise row:
    - Check if there is a Strength_Exercises row linked to that exercise_id; if so, load strength details.
    - Check if there is a Cardio_Exercises row linked; if so, load cardio details and any Run or Bike_Rides row.
4. Display a consolidated list showing for each exercise:
   - date, name, rpe, and subtype fields (weight/sets/reps OR avg_hr/time/distance/wattage).
5. Allow the user to filter by date range or type.
## K. List clients for a trainer (join)
1. Ask for trainer_id (or let user pick trainer by name).
2. Validate trainer exists.
3. Steps:
   - Fetch TrainerClients rows for trainer_id where client_end_date is NULL or client_end_date >= today for active clients.
   - For each TrainerClients row, fetch the Member’s first and last name.
4. Display a table: member_id | member name | start date | end date | notes.
## L. Aggregation: Total payments per member / overall revenue
1. To compute total payments for a member:
   - Ask for member_id (optional — if none, compute for all members).
  - Sum the amount values in Payments where member_id matches.
  - Return the sum.
2. To compute total revenue for the gym:
   - Sum all amount values in Payments across the table.
  - Return the total.
## M. Aggregation: Average RPE per member or overall
1. Ask whether the user wants per-member or overall average.
2. For per-member:
   - For each member, find all Exercises rows for that member and compute the average of rpe.
3. For overall:
   - Compute the average of rpe across all Exercises rows.
4. Return and display results in a simple table.
## N. Aggregation: Maximum weight lifted by a member
1. Ask for the member_id.
2. Steps:
   - Find Strength_Exercises rows joined to Exercises for that member.
  - Find the maximum exercise_weight value across those rows.
3. Return the max weight and which exercise/date it occurred on.
## O. Aggregation: Average distance for runs per member
1. Ask whether to calculate for a specific member or all members.
2. For each targeted member:
   - Find Runs rows joined through Cardio_Exercises → Exercises → Members.
  - Compute average(distance) across those runs.
3. Display member_id, name, and average distance.
## P. Reporting and UI behavior suggestions
1. Provide simple UI pages or dialogs for:
   - Add/Edit/Delete Member
   - Add/Edit/Delete Exercise
   - Assign/Unassign Trainer to Member
   - Add Payment
   - Reports: Payments, Trainer Clients, Exercise History, Aggregates (avg RPE, total revenue)
2. For each report allow filters (date range, member, trainer, exercise type).
3. Always show loading feedback during long queries and confirm dialogs before delete actions.
## Q. Error handling & logging
1. For each function, catch database errors and return clear error messages to the user.
2. Log every fatal error with a timestamp, operation name, user id, and error details (for admin troubleshooting).
3. If a transaction fails, roll back and show a friendly message: “Operation failed. No data was changed.”