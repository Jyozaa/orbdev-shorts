from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).parent));import editorialize_discovery as e
def main():
    hot={"score":9.2,"lanes":["hot_emerging","creator_radar"],"creators":["Fireship"],"sourceNames":["GitHub","Fireship"],"signals":["github-trending","hacker-news"]};cold={"score":7.3,"lanes":["major_news"],"creators":[],"sourceNames":["Example"],"signals":[]}
    assert e.heat_bonus(hot)>e.heat_bonus(cold)
    state={"decisions":[{"clusterId":"x","decision":"rejected","discoveryScore":8.0,"decidedAt":datetime.now(ZoneInfo("Europe/London")).isoformat()}]}
    assert not e.should_recheck({"clusterId":"x","score":8.1},state,datetime.now(ZoneInfo("Europe/London")),24,.6)[0]
    assert e.should_recheck({"clusterId":"x","score":8.8},state,datetime.now(ZoneInfo("Europe/London")),24,.6)[0]
    print("Editorial logic regression checks passed")
if __name__=="__main__":main()
