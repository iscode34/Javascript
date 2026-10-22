//Create a rectangle calculator


const rectangle = {
    width: 10,
    height: 5,

    getArea: function() {
        return this.width * this.height;
    },

    getPerimeter: function() {
        return 2 * (this.width + this.height);
    }
};

console.log("Width:", rectangle.width);
console.log("Height:", rectangle.height);
console.log("Area:", rectangle.getArea());
console.log("Perimeter:", rectangle.getPerimeter());



//Work with nested objects

const employee = {
    name: "Budi",
    address: {
        street: "Jl. Merdeka No. 10",
        city: "Jakarta",
        postalCode: "10110"
    }
};

employee.address.city = "Bandung";

console.log("Employee:", employee.name);
console.log("Street:", employee.address.street);
console.log("City:", employee.address.city);
console.log("Postal Code:", employee.address.postalCode);
