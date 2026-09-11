export function Checkout() {
  return (
    <main data-screen="mobile-checkout">
      <div data-context="checkout-commitment">
        <section data-region="order-summary">
          <span data-field="order-total">$42.00</span>
          <button data-action="promo-code">Have a promo code?</button>
        </section>
        <section data-region="payment-entry">
          <input aria-label="Card number" />
          <button data-action="submit-order">Place order</button>
        </section>
      </div>
    </main>
  );
}
