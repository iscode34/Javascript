const studentName = "Andi";
const assignment = 80;
const midterm = 75;
const finalExam = 90;

const finalScore =
  (assignment * 30) / 100 +
  (midterm * 30) / 100 +
  (finalExam * 40) / 100;

const status = finalScore >= 70 ? "Passed" : "Failed";

const category =
  finalScore >= 85 ? "Excellent" :
  finalScore >= 70 ? "Good" :
  "Failed";

console.log(`Student: ${studentName}
Assignment: ${assignment}
Midterm: ${midterm}
Final Exam: ${finalExam}
Final Score: ${finalScore}
Status: ${status}
Category: ${category}`);