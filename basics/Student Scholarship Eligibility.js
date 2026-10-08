const checkScholarship = (studentName, averageScore, attendance, familyIncome, organizationMember) => {
  const basicRequirement = averageScore >= 80 && attendance >= 90;
  const basicStatus = basicRequirement ? "Passed" : "Failed";

  const category = basicRequirement
    ? (familyIncome <= 3000000 && organizationMember
        ? "Category A"
        : (familyIncome <= 5000000 && organizationMember
            ? "Category B"
            : "Not Eligible"))
    : "Not Eligible";

  console.log(`Student: ${studentName}
Average Score: ${averageScore}
Attendance: ${attendance}%
Family Income: Rp${familyIncome}
Organization Member: ${organizationMember}

Basic Requirement: ${basicStatus}
Scholarship Category: ${category}
---`);
};

checkScholarship("Siti", 86, 92, 4000000, true);
checkScholarship("Andi", 75, 95, 2000000, true);
checkScholarship("Rina", 90, 88, 2000000, true);