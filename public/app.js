const $ = id => document.getElementById(id);
let students = [], current = null;
const simulated = new Set();
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
async function api(path, body) {
  const response = await fetch(path, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}
function render() {
  $('rows').replaceChildren();
  const visible = students.filter(s => s.name.toLowerCase().includes($('search').value.toLowerCase()));
  for (const s of visible) {
    const row = element('tr');
    const identity = element('td');
    identity.append(element('span', s.name, 'student'), element('small', s.phone || 'No parent number'));
    row.append(identity);
    for (const mark of Object.values(s.marks)) row.append(element('td', mark ?? '—'));
    const status = element('td');
    status.append(element('span', simulated.has(s.id) ? 'Simulated' : s.warnings.length ? 'Review record' : 'Ready to review', 'badge ' + (simulated.has(s.id) ? 'done' : s.warnings.length ? 'warn' : '')));
    const action = element('td');
    const button = element('button', 'Send WhatsApp', 'secondary');
    button.addEventListener('click', () => preview([s.id]));
    action.append(button); row.append(status, action); $('rows').append(row);
  }
  if (!visible.length) { const row=element('tr'); const cell=element('td','No students match your search.'); cell.colSpan=7; row.append(cell); $('rows').append(row); }
  $('sent').textContent = simulated.size;
}
async function preview(ids) {
  $('error').textContent = '';
  const request = {studentIds:ids, assessment:$('assessment').value, counsellor:$('counsellor').value, country:$('country').value};
  try {
    const data = await api('/api/preview', request);
    current = request;
    $('dialog-title').textContent = ids.length > 1 ? `Review ${ids.length} parent messages` : 'Review parent message';
    $('previews').replaceChildren(); $('result').textContent = '';
    for (const item of data.results) {
      const card = element('article', undefined, 'preview');
      card.append(element('h3', item.name));
      if (item.status === 'failed') card.append(element('p', item.detail, 'warning'));
      else {
        card.append(element('p', '+' + item.phone));
        for (const warning of item.warnings) card.append(element('p', warning, 'warning'));
        card.append(element('pre', item.message));
        const link = element('a', 'Open draft in WhatsApp ↗', 'link secondary');
        link.href=item.url; link.target='_blank'; link.rel='noopener noreferrer'; card.append(link);
      }
      $('previews').append(card);
    }
    $('simulate').disabled = !data.results.some(item => item.status === 'ready');
    $('simulate').textContent = ids.length > 1 ? 'Simulate all sends' : 'Simulate send';
    if (!$('dialog').open) $('dialog').showModal();
  } catch (error) { $('error').textContent=error.message; }
}
$('simulate').addEventListener('click', async () => {
  $('simulate').disabled=true;
  try {
    const data=await api('/api/send',current);
    const successes=data.results.filter(item => item.status === 'simulated');
    successes.forEach(item => simulated.add(item.studentId));
    $('result').textContent=`${successes.length} message(s) simulated. ${data.results.length-successes.length} failed. No messages were sent to parents.`;
    render();
  } catch(error) { $('result').textContent=error.message; $('simulate').disabled=false; }
});
$('close').addEventListener('click', () => $('dialog').close());
$('search').addEventListener('input',render);
$('all').addEventListener('click', () => preview(students.map(s => s.id)));
api('/api/students').then(data => {
  students=data.students; $('count').textContent=students.length;
  $('reviews').textContent=students.filter(s => s.warnings.length).length;
  $('source').textContent=data.source; $('all').disabled=!students.length; render();
}).catch(error => { $('error').textContent='Could not load the workbook: '+error.message; $('source').textContent='Workbook unavailable'; });
