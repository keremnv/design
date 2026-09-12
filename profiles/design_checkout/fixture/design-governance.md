# Mobile checkout design governance

The mobile checkout task governs a small set of consequential design
questions. These statements describe which questions must be determined; they
do not select the answer to any question.

## Availability

During payment, critical order information must have an explicit availability
determination in the mobile checkout surface.

- Subject: order-summary region
- Activity: payment-entry region
- Context: mobile-checkout surface

## Priority

At purchase commitment, hierarchy between critical purchase information and
promotional interactions must have an explicit determination.

- More: order-total field
- Less: promo-code interaction
- Context: checkout-commitment context

## Goal support

Critical checkout information may have an explicit relationship to purchase
confidence.

- Subject: order-summary region
- Goal: purchase-confidence goal
- Context: checkout-commitment context
