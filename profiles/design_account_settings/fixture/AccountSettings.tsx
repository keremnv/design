export function AccountSettings() {
  return (
    <main data-screen="account-settings">
      <section data-region="profile-settings">
        <input data-field="display-name" />
        <section data-region="email-preferences">
          <input aria-label="Product email preferences" />
        </section>
        <button data-action="save-changes">Save changes</button>
      </section>
      <section data-region="danger-zone">
        <button data-action="delete-account">Delete account</button>
        <div data-context="delete-confirmation">
          <button data-action="confirm-delete">Confirm deletion</button>
        </div>
        <p data-context="account-deleted">Account deleted</p>
      </section>
    </main>
  );
}
