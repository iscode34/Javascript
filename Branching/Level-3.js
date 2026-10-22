//Build an invertory system

const products = [
    { name: "laptop", price: 450, stock: 3},
    { name: "Mouse", price: 50, stock: 15 },
    { name: "keyboard", price: "150", stock: "55"}
];

let totalValue = 0;
let lowStock = [];

for (let i = 0; i < products.length; i++) {
    totalValue = totalValue +
    (products[i].price * products[i].stock);

    if (products[i].stock < 5){
        lowStock.push(products[i].name);
    }
}

console.log("Total Inventory Value:", totalValue);
console.log("Inventory Below 5:", lowStock);



//Create a shopping cart



const cart = {
    items: [],

    addProduct: function(id, name, price, quantity) {
        for (let i = 0; i < this.items.length; i++) {
            if (this.items[i].id === id) {
                this.items[i].quantity += quantity;
                return;
            }
        }

        this.items.push({
            id: id,
            name: name,
            price: price,
            quantity: quantity
        });
    },

    removeProduct: function(id) {
        for (let i = 0; i < this.items.length; i++) {
            if (this.items[i].id === id) {
                this.items.splice(i, 1);
                return;
            }
        }
    },

    getTotal: function() {
        let total = 0;

        for (let i = 0; i < this.items.length; i++) {
            total += this.items[i].price *
                     this.items[i].quantity;
        }

        return total;
    }
};

cart.addProduct(1, "Book", 10, 2);
cart.addProduct(2, "Pen", 2, 3);
cart.addProduct(1, "pencil", 15, 10);

console.log("Cart Items:", cart.items);
console.log("Total:", cart.getTotal());

cart.removeProduct(2);

console.log("After Removing Pen:", cart.items);
console.log("New Total:", cart.getTotal());
