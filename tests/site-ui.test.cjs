const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../templates/site-ui.js'),'utf8');
function setup(isMobile){
 const events={},attrs={'aria-expanded':'true'},media={matches:isMobile,addEventListener(name,handler){events.media=handler;}};
 const button={hidden:true,setAttribute(k,v){attrs[k]=v;},getAttribute(k){return attrs[k];},addEventListener(name,handler){events.button=handler;}};
 const links={hidden:false,addEventListener(name,handler){events.links=handler;}};
 const nav={querySelector(query){return query==='[data-nav-toggle]'?button:links;}};
 vm.runInNewContext(source,{document:{querySelector(){return nav;}},window:{matchMedia(){return media;}}});
 return {events,attrs,media,button,links};
}
test('phone navigation begins collapsed and can be expanded by its button',()=>{
 const ui=setup(true);
 assert.equal(ui.button.hidden,false);assert.equal(ui.links.hidden,true);assert.equal(ui.attrs['aria-expanded'],'false');
 ui.events.button();assert.equal(ui.links.hidden,false);assert.equal(ui.attrs['aria-expanded'],'true');
 ui.events.button();assert.equal(ui.links.hidden,true);
});
test('choosing a day closes the phone navigation',()=>{
 const ui=setup(true);ui.events.button();ui.events.links({target:{closest(){return {};}}});
 assert.equal(ui.links.hidden,true);assert.equal(ui.attrs['aria-expanded'],'false');
});
test('desktop navigation stays visible when the viewport changes',()=>{
 const ui=setup(true);ui.media.matches=false;ui.events.media();
 assert.equal(ui.button.hidden,true);assert.equal(ui.links.hidden,false);assert.equal(ui.attrs['aria-expanded'],'true');
});
