const fs = require('fs');

const rawData = fs.readFileSync('data.js', 'utf8');
const jsonMatch = rawData.match(/window\.CONTRACT_DATA\s*=\s*(\[.*?\]);/s);
const data = JSON.parse(jsonMatch[1]);

const monthColumns = Object.keys(data[0] || {})
    .filter(k => /^[A-Z]{3}\/\d{2}$/.test(k))
    .sort((a, b) => {
        const months = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
        const [mA, yA] = a.split('/');
        const [mB, yB] = b.split('/');
        if (yA !== yB) return yA - yB;
        return months.indexOf(mA) - months.indexOf(mB);
    });

console.log("Month columns:", monthColumns.join(", "));

const filterMonth = 'FEV/26';
const filterMonthIndex = monthColumns.indexOf(filterMonth);
const monthMap = {'JAN':'01', 'FEV':'02', 'MAR':'03', 'ABR':'04', 'MAI':'05', 'JUN':'06', 'JUL':'07', 'AGO':'08', 'SET':'09', 'OUT':'10', 'NOV':'11', 'DEZ':'12'};
const parts = filterMonth.split('/');
const year = '20' + parts[1];
const monthNum = monthMap[parts[0]];
const daysInMonth = new Date(parseInt(year), parseInt(monthNum), 0).getDate();
const monthStart = `${year}-${monthNum}-01`;
const monthEnd = `${year}-${monthNum}-${daysInMonth}`;

const emtel = data.find(c => c['SUBCONTRATADO'] && c['SUBCONTRATADO'].includes('EMTEL'));

if (!emtel) {
    console.log("EMTEL not found!");
    process.exit(1);
}

const parseDateStr = (dateStr) => {
    if (!dateStr) return null;
    const dashMatch = String(dateStr).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (dashMatch) return `${dashMatch[1]}-${dashMatch[2]}-${dashMatch[3]}`;
    return String(dateStr);
};

const parseNumber = (val) => {
    if (typeof val === 'number') return isNaN(val) ? 0 : val;
    if (!val || val === '-' || val === ' ') return 0;
    let clean = val.toString().replace(/[\sR\$]/g, '');
    if (clean.includes(',') && clean.includes('.')) {
        clean = clean.replace(/\./g, '').replace(',', '.');
    } else if (clean.includes(',')) {
        clean = clean.replace(',', '.');
    }
    const num = parseFloat(clean);
    return isNaN(num) ? 0 : num;
};

// Simulate get contracts
let valid = true;
const dInicio = parseDateStr(emtel['INICIO_CONTRATO']);
const dFim = parseDateStr(emtel['TERMINO_CONTRATO']);
console.log("dInicio:", dInicio, "dFim:", dFim, "monthStart:", monthStart, "monthEnd:", monthEnd);

if (dInicio && dInicio > monthEnd) { console.log("Filtered by dInicio"); valid = false; }
if (dFim && dFim < monthStart) { console.log("Filtered by dFim"); valid = false; }

console.log("Valid after date bounds:", valid);

let baseAcumuladoNoMes = parseNumber(emtel[filterMonth]);
let prevMonthStr = filterMonthIndex > 0 ? monthColumns[filterMonthIndex - 1] : null;
let prevM = prevMonthStr ? parseNumber(emtel[prevMonthStr]) : 0;
let tempMedido = baseAcumuladoNoMes - prevM;

console.log("baseAcumuladoNoMes:", baseAcumuladoNoMes, "prevM:", prevM, "tempMedido:", tempMedido);

const didStartThisMonth = dInicio && (dInicio >= monthStart && dInicio <= monthEnd);
console.log("didStartThisMonth:", didStartThisMonth);

if (tempMedido <= 0 && !didStartThisMonth) {
    console.log("Filtered by zero production and NOT started this month");
    valid = false;
}

console.log("Final Valid:", valid);
