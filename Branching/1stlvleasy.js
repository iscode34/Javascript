//level 1(Even/Odd)

let number= 7;
if (number % 2 === 0) {
     console.log("even");
} else {
    console.log("odd");
}

//level 2(grade)

let score = 35;

if (score >=  80 && score <= 100){
    console.log("Grade A");
} else if (score >=70){
    console.log("Grade B");
} else if (score >=60){
    console.log("Grade C");
} else if (score >=50){
    console.log("Grade D");
} else  {
    console.log("Grade E");
}

//level 3(Student Passing Check)

let score1 = 60;
let attendance = 80;

if (score1>=60 && attendance >= 75){
    console.log("Pass");
} else {
    console.log("Fail");
}


//Level 4 ( student assessment system)

let score2 = 65;
let attendance2 = 70;
let assignments =73;

if (score2 >= 60 && attendance2 >= 75 && assignments >= 80) {
    console.log("PASS");
} else {
    console.log("Fail");

    if (score2 <= 60) {
        console.log("Reason: Score is below 60");
    } 
    if (attendance2 <= 75) {
        console.log("Reason: Attendance is lower than passing requirement");
    }
    if (assignments <= 80){
        console.log("Reason: Assignments are below 80%");
    }
 }