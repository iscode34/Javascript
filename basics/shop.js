const customerName = "Budi";
const productPrice = 150000;
const quantity = 3;
const discountPercent = 10;
const shippingCost = 20000;

function calculateTotal(price, quantity, discount) {
  const subtotal = price * quantity;
  const discountAmount = (subtotal * discount) / 100;
  const totalBeforeShipping = subtotal - discountAmount;
  return totalBeforeShipping;
}

const calculateShipping = (total) => {
  return total >= 500000 ? 0 : shippingCost;
};

const subtotal = productPrice * quantity;
const discount = (subtotal * discountPercent) / 100;
const afterDiscount = calculateTotal(productPrice, quantity, discountPercent);
const shipping = calculateShipping(afterDiscount);
const totalPayment = afterDiscount + shipping;

console.log(`Customer: ${customerName}
Product Price: Rp${productPrice}
Quantity: ${quantity}
Subtotal: Rp${subtotal}
Discount: Rp${discount}
After Discount: Rp${afterDiscount}
Shipping: Rp${shipping}
Total Payment: Rp${totalPayment}`);