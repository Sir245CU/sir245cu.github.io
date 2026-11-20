// Estrae l'oggetto DATA (dati di mercato incorporati) dall'HTML dell'app e lo scrive come JSON.
// uso: node estrai_data.js index.html base.json
const fs=require('fs');const s=fs.readFileSync(process.argv[2],'utf8');
const i=s.indexOf('var DATA={');if(i<0)throw new Error('DATA non trovato');
let j=i+'var DATA='.length,d=0,q=null,esc=false,k=j;
for(;k<s.length;k++){const c=s[k];
  if(q){if(esc)esc=false;else if(c==='\\')esc=true;else if(c===q)q=null;continue}
  if(c==='/'&&s[k+1]==='/'){k=s.indexOf('\n',k);continue}
  if(c==='/'&&s[k+1]==='*'){k=s.indexOf('*/',k)+1;continue}
  if(c==="'"||c==='"'||c==='`'){q=c;continue}
  if(c==='{')d++;else if(c==='}'){d--;if(!d)break}}
const lit=s.slice(j,k+1);const o=(new Function('return ('+lit+')'))();
fs.writeFileSync(process.argv[3],JSON.stringify(o));
console.log('DATA',o.asof,Object.keys(o).join(','));
