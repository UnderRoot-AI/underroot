import { useEffect } from "react";
import { useLanguageStore, type Language } from "../store/languageStore";
import { GLOBAL_TRANSLATIONS } from "./globalTranslations";
const originals = new WeakMap<Text,string>();
const attrs = new WeakMap<Element,Map<string,string>>();
const ATTRS=["placeholder","aria-label","title"];
function apply(language:Language){
 const dict=GLOBAL_TRANSLATIONS[language]||{}; const root=document.body; if(!root)return;
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT); let n:Node|null;
 while((n=walker.nextNode())){const t=n as Text, p=t.parentElement; if(!p||["SCRIPT","STYLE","NOSCRIPT","TEXTAREA"].includes(p.tagName))continue; if(!originals.has(t))originals.set(t,t.nodeValue||""); const o=originals.get(t)||"", key=o.trim(); if(!key)continue; const v=language==="en"?key:dict[key]; if(v){const lead=o.match(/^\s*/)?.[0]||"",trail=o.match(/\s*$/)?.[0]||"";t.nodeValue=lead+v+trail;}}
 root.querySelectorAll<HTMLElement>("*").forEach(el=>{if(!attrs.has(el))attrs.set(el,new Map());const m=attrs.get(el)!;for(const a of ATTRS){const v=el.getAttribute(a);if(v!==null&&!m.has(a))m.set(a,v);const o=m.get(a);if(!o)continue;const x=language==="en"?o:dict[o];if(x)el.setAttribute(a,x);}});
}
export function useGlobalTranslation(){const language=useLanguageStore(s=>s.language);useEffect(()=>{let timer:number|undefined;const run=()=>{clearTimeout(timer);timer=window.setTimeout(()=>apply(language),0)};run();const mo=new MutationObserver(run);mo.observe(document.body,{childList:true,subtree:true});return()=>{mo.disconnect();clearTimeout(timer)}},[language]);}
