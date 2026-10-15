const readline = require("readline");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Level 1: Positive / Negative / Zero
rl.question("Enter a number: ", function(input1) {
  let number = Number(input1);

  if (number > 0) {
    console.log("Positive");
  } else if (number < 0) {
    console.log("Negative");
  } else {
    console.log("Zero");
  }

  // Level 2: Shopping Discount
  rl.question("Enter total purchase: ", function(input2) {
    let total = Number(input2);
    let discount = 0;

    if (total >= 1000000) {
      discount = 0.20;
    } else if (total >= 500000) {
      discount = 0.10;
    } else if (total >= 250000) {
      discount = 0.05;
    }

    let finalPrice = total - (total * discount);
    console.log("Final price: " + finalPrice);

    // Level 3: Traffic Light
    rl.question("Enter traffic light color: ", function(input3) {
      let color = input3.toLowerCase();

      if (color === "red") {
        console.log("Stop");
      } else if (color === "yellow") {
        console.log("Get Ready");
      } else if (color === "green") {
        console.log("Go");
      } else {
        console.log("Invalid Color");
      }

      // Level 4: Parking Fee
      rl.question("Enter parking hours: ", function(input4) {
        let hours = Number(input4);
        let fee = 0;

        if (hours <= 0) {
          console.log("Invalid hours");
        } else {
          if (hours === 1) {
            fee = 5000;
          } else {
            fee = 5000 + ((hours - 1) * 3000);
          }

          if (fee > 20000) {
            fee = 20000;
          }

          console.log("Parking fee: Rp" + fee);
        }

        rl.close();
      });
    });
  });
});