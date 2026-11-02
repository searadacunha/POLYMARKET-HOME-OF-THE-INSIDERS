"""Phase 9 : gel du modèle de contexte seul (p_ctx), entraîné sur TRAIN uniquement, à l'identique de p9_backtest.py (random_state=9).
Il sert au détecteur (market_context_score). Vérifie que les prédictions reproduisent p_ctx de events_scored.pkl."""
import numpy as np,pandas as pd,pickle,os,shutil
from sklearn.ensemble import HistGradientBoostingClassifier
src=open('p9_train.py').read(); exec(src[:src.index('EV=pd.read_pickle')]); exec(src[src.index('FEAT='):src.index("TR=EV[")])
EV=pd.read_pickle('p9/events_scored.pkl')
CTX=['dpre_1m','dpre_10m','dpre_60m','act_10m','activity_ratio','p_before','hours_to_end','cat_politics','cat_geo','cat_macro']
ok=EV.p_before.notna(); trm=(EV.split=='TRAIN')&EV.is_FAE&~EV.FOLLOW&ok
Xa=X(EV)
m=HistGradientBoostingClassifier(random_state=9).fit(Xa.loc[trm,CTX],EV.loc[trm,'LEAD60'].astype(int))
p=m.predict_proba(Xa.loc[ok,CTX])[:,1]
print('écart max avec p_ctx du backtest',float(np.abs(p-EV.loc[ok,'p_ctx'].values).max()))
D='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase9/modeles/'; os.makedirs(D,exist_ok=True)
pickle.dump({'model':m,'features':CTX},open('p9/frozen_model_ctx.pkl','wb'))
for f in ('frozen_model.pkl','frozen_model_wallet.pkl','frozen_model_ctx.pkl','frozen_spec.json'): shutil.copy2('p9/'+f,D+f)
print(os.listdir(D))
