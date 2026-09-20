# Account settings design governance

The account settings task governs the following questions. These statements
identify determinations to make; they do not select the answer.

## Confirmation before deletion

For an irreversible destructive action, determine whether explicit confirmation
is required before the consequence occurs.

- Action: delete-account interaction
- Consequence: account-deleted context
- Context: account-settings surface

## Consequence distinction

Routine preference editing and irreversible account deletion require a distinct
consequence treatment.

- Routine: save-changes interaction
- Destructive: delete-account interaction
- Context: account-settings surface
