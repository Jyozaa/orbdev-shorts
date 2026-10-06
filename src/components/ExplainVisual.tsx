import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {ExplainVisual as ExplainSpec} from '../types';

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

const Dot: React.FC<{x:number;y:number;size?:number;opacity?:number}> = ({x,y,size=22,opacity=1}) => (
  <div style={{
    position:'absolute',left:x-size/2,top:y-size/2,width:size,height:size,
    borderRadius:'50%',background:'#fff',opacity
  }}/>
);

const Network: React.FC<{layers:number[];left:number;top:number;width:number;height:number;reveal:number;scale?:number}> =
({layers,left,top,width,height,reveal,scale=1}) => {
  const points:{x:number;y:number}[][] = layers.map((count, li) => {
    const x = left + (layers.length === 1 ? width/2 : li * width/(layers.length-1));
    return Array.from({length:count}, (_,i) => ({
      x,
      y: top + (count===1 ? height/2 : i*height/(count-1))
    }));
  });
  return <div style={{position:'absolute',inset:0,transform:`scale(${scale})`}}>
    <svg width="1080" height="1920" style={{position:'absolute',inset:0}}>
      {points.slice(0,-1).flatMap((layer,li)=>
        layer.flatMap((a,ai)=>points[li+1].map((b,bi)=>(
          <line key={`${li}-${ai}-${bi}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
            stroke="rgba(255,255,255,.32)" strokeWidth="3"
            strokeDasharray="900" strokeDashoffset={900*(1-reveal)}/>
        )))
      )}
    </svg>
    {points.flat().map((p,i)=><Dot key={i} x={p.x} y={p.y} size={24} opacity={reveal}/>)}
  </div>;
};

export const ExplainVisual: React.FC<{visual: ExplainSpec}> = ({visual}) => {
  const frame=useCurrentFrame();
  const {fps,durationInFrames}=useVideoConfig();
  const p=clamp01(frame/Math.max(1,durationInFrames-1));
  const enter=spring({frame,fps,config:{damping:18,stiffness:160,mass:.65}});
  const camera=1+0.025*p;
  const labels=visual.labels ?? [];
  const variant=((visual.variant ?? 0)%6+6)%6;

  if(visual.mode==='pixel-upscale'){
    const leftReveal=clamp01(p/0.35);
    const rightReveal=clamp01((p-0.28)/0.5);
    const cols=5, rows=5;
    const fineCols=10, fineRows=10;
    return <AbsoluteFill style={{background:'#000',color:'#fff',fontFamily:'Arial',transform:`scale(${camera})`}}>
      <div style={{position:'absolute',left:92,top:560,width:320,height:320}}>
        {Array.from({length:cols*rows},(_,i)=><div key={i} style={{
          position:'absolute',
          left:(i%cols)*64,top:Math.floor(i/cols)*64,width:56,height:56,
          background:i%3===0?'#fff':'rgba(255,255,255,.35)',
          opacity:leftReveal,transform:`scale(${.65+.35*enter})`
        }}/>)}
      </div>
      <div style={{position:'absolute',left:460,top:680,fontSize:90,fontWeight:900,opacity:clamp01((p-.15)/.25)}}>→</div>
      <div style={{position:'absolute',right:88,top:520,width:400,height:400}}>
        {Array.from({length:fineCols*fineRows},(_,i)=><div key={i} style={{
          position:'absolute',
          left:(i%fineCols)*40,top:Math.floor(i/fineCols)*40,width:35,height:35,
          background:(i*7)%11<5?'#fff':'rgba(255,255,255,.48)',
          opacity:rightReveal,transform:`scale(${.55+.45*rightReveal})`
        }}/>)}
      </div>
      <div style={{position:'absolute',left:140,top:930,fontSize:34,fontWeight:850,opacity:leftReveal}}>{labels[0]??'LOW RES'}</div>
      <div style={{position:'absolute',right:160,top:950,fontSize:34,fontWeight:850,opacity:rightReveal}}>{labels[1]??'UPSCALED'}</div>
    </AbsoluteFill>;
  }

  if(visual.mode==='network-shrink'){
    const switchP=clamp01((p-.36)/.44);
    const from=visual.fromLayers ?? [5,4,4,3];
    const to=visual.toLayers ?? [3,3,2];
    return <AbsoluteFill style={{background:'#000',color:'#fff',fontFamily:'Arial',transform:`scale(${camera})`}}>
      <div style={{opacity:1-switchP,transform:`translateX(${-80*switchP}px) scale(${1-.15*switchP})`}}>
        <Network layers={from} left={150} top={560} width={760} height={610} reveal={Math.min(1,p*3)} />
      </div>
      <div style={{opacity:switchP,transform:`translateX(${80*(1-switchP)}px) scale(${.8+.2*switchP})`}}>
        <Network layers={to} left={235} top={620} width={610} height={500} reveal={switchP} />
      </div>
      <div style={{position:'absolute',left:0,right:0,top:1260,textAlign:'center',fontSize:38,fontWeight:900}}>
        <span style={{opacity:1-switchP}}>{labels[0]??'LARGE NETWORK'}</span>
        <span style={{opacity:switchP,position:'absolute',left:0,right:0}}>{labels[1]??'SMALLER NETWORK'}</span>
      </div>
    </AbsoluteFill>;
  }

  if(visual.mode==='capacity'){
    const load=Math.max(0,Math.min(100,visual.load ?? 95));
    const fill=Math.min(load/100,1)*enter;
    const danger=load>=90;
    return <AbsoluteFill style={{background:'#000',color:'#fff',fontFamily:'Arial',alignItems:'center',justifyContent:'center'}}>
      <div style={{width:760,height:580,border:'5px solid #fff',borderRadius:54,position:'relative',
        transform:`scale(${.82+.18*enter}) rotate(${(1-enter)*-3}deg)`}}>
        {Array.from({length:9},(_,i)=><div key={i} style={{
          position:'absolute',width:30,height:70,background:'rgba(255,255,255,.55)',
          left:70+i*78,top:i%2===0?-72:582
        }}/>)}
        <div style={{position:'absolute',left:70,right:70,top:105,fontSize:54,fontWeight:950,textAlign:'center'}}>{labels[0]??'GPU'}</div>
        <div style={{position:'absolute',left:80,right:80,bottom:120,height:150,border:'4px solid rgba(255,255,255,.55)',borderRadius:26,overflow:'hidden'}}>
          <div style={{height:'100%',width:`${fill*100}%`,background:'#fff',transformOrigin:'left'}}/>
        </div>
        <div style={{position:'absolute',left:0,right:0,bottom:45,textAlign:'center',fontSize:42,fontWeight:900}}>
          {Math.round(load*enter)}%{danger&&p>.55?'  ⚠':''}
        </div>
      </div>
    </AbsoluteFill>;
  }

  if(visual.mode==='stability'){
    const stable=clamp01((p-.45)/.35);
    const jitter=(1-stable)*Math.sin(frame*1.9)*22;
    return <AbsoluteFill style={{background:'#000',color:'#fff',fontFamily:'Arial'}}>
      <div style={{position:'absolute',left:90,top:570,width:390,height:480,border:'4px solid rgba(255,255,255,.7)',
        transform:`translate(${jitter}px,${-jitter*.45}px) rotate(${jitter*.035}deg)`}}>
        {Array.from({length:9},(_,i)=><div key={i} style={{position:'absolute',left:30+(i%3)*110,top:35+Math.floor(i/3)*125,width:75,height:75,border:'3px solid #fff',opacity:.7}}/>)}
      </div>
      <div style={{position:'absolute',left:505,top:760,fontSize:86,fontWeight:900,opacity:clamp01((p-.2)/.2)}}>→</div>
      <div style={{position:'absolute',right:90,top:570,width:390,height:480,border:'4px solid #fff',
        transform:`scale(${.9+.1*stable})`}}>
        {Array.from({length:9},(_,i)=><div key={i} style={{position:'absolute',left:30+(i%3)*110,top:35+Math.floor(i/3)*125,width:75,height:75,background:'#fff',opacity:.55+.45*stable}}/>)}
      </div>
      <div style={{position:'absolute',left:150,top:1090,fontSize:34,fontWeight:850}}>{labels[0]??'SHIMMER'}</div>
      <div style={{position:'absolute',right:190,top:1090,fontSize:34,fontWeight:850}}>{labels[1]??'STABLE'}</div>
    </AbsoluteFill>;
  }

  if(visual.mode==='pipeline'){
    const stages=(visual.stages ?? labels).slice(0,5);
    return <AbsoluteFill style={{background:'#000',color:'#fff',fontFamily:'Arial',transform:`scale(${camera})`}}>
      <div style={{
        position:'absolute',
        left: variant%3===1 ? 265 : variant%3===2 ? 120 : 90,
        right: variant%3===1 ? 265 : variant%3===2 ? 120 : 90,
        top: variant%3===1 ? 410 : variant%3===2 ? 565 : 760,
        height: variant%3===1 ? 1000 : variant%3===2 ? 550 : 300,
        display:'flex',
        flexDirection:variant%3===1?'column':'row',
        alignItems:'center',justifyContent:'space-between',
        transform:variant%3===2?'rotate(-8deg)':undefined
      }}>
        {stages.map((stage,i)=>{
          const r=spring({frame,fps,delay:i*6,config:{damping:18,stiffness:175}});
          return <React.Fragment key={stage+i}>
            <div style={{
              width:variant%2?208:190,height:variant%2?150:190,borderRadius:variant%2?22:'50%',
              border:'4px solid #fff',display:'flex',alignItems:'center',justifyContent:'center',
              fontSize:Math.max(24,46-stage.length*1.35),fontWeight:950,textAlign:'center',opacity:r,
              transform:`scale(${.7+.3*r})`,padding:16,boxSizing:'border-box'
            }}>{stage}</div>
            {i<stages.length-1&&<div style={{height:variant%3===1?44:5,width:variant%3===1?5:undefined,flex:variant%3===1?undefined:1,margin:variant%3===1?'8px 0':'0 14px',background:'#fff',transformOrigin:'left',transform:`scale${variant%3===1?'Y':'X'}(${clamp01((p-.12*i)*1.8)})`}}/>}
          </React.Fragment>;
        })}
      </div>
      <div style={{position:'absolute',top:variant%3===1?500+clamp01(p)*820:830,left:variant%3===1?535:95+clamp01(p)*820,width:24,height:24,borderRadius:'50%',background:'#fff',boxShadow:'0 0 25px #fff'}}/>
    </AbsoluteFill>;
  }

  const nodes=(visual.nodes ?? labels).slice(0,6);
  const center=visual.center ?? 'MODEL';
  return <AbsoluteFill style={{background:'#000',color:'#fff',fontFamily:'Arial',transform:`scale(${camera})`}}>
    <svg width="1080" height="1920" style={{position:'absolute',inset:0}}>
      {nodes.map((_,i)=>{
        const a=-Math.PI/2+i*Math.PI*2/nodes.length;
        const orbit=variant%3===0?350:variant%3===1?260:410;
        const x=540+Math.cos(a)*orbit,y=860+Math.sin(a)*(variant%3===1?520:variant%3===2?245:350);
        return <line key={i} x1="540" y1="860" x2={x} y2={y} stroke="rgba(255,255,255,.55)" strokeWidth="4"
          strokeDasharray="500" strokeDashoffset={500*(1-clamp01((p-.08*i)*1.8))}/>;
      })}
    </svg>
    <div style={{position:'absolute',left:420,top:740,width:240,height:240,borderRadius:'50%',background:'#fff',color:'#000',
      display:'flex',alignItems:'center',justifyContent:'center',fontSize:42,fontWeight:950,transform:`scale(${.75+.25*enter})`}}>{center}</div>
    {nodes.map((node,i)=>{
      const a=-Math.PI/2+i*Math.PI*2/nodes.length;
      const x=540+Math.cos(a)*350,y=860+Math.sin(a)*350;
      const r=spring({frame,fps,delay:6+i*4,config:{damping:18,stiffness:175}});
      return <div key={node+i} style={{position:'absolute',left:x-90,top:y-90,width:180,height:180,borderRadius:'50%',border:'3px solid #fff',
        display:'flex',alignItems:'center',justifyContent:'center',fontSize:28,fontWeight:900,textAlign:'center',opacity:r,transform:`scale(${.7+.3*r})`,padding:16,boxSizing:'border-box'}}>{node}</div>;
    })}
  </AbsoluteFill>;
};
