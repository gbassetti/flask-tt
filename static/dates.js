const d = new Date();
d.setDate(d.getDate() - 8);
startdate.value = d.toISOString().split("T")[0];

const f = new Date();
f.setDate(f.getDate() - 1);
enddate.value = f.toISOString().split("T")[0];