import os

def KillBlueRed(ID_SKIN, BlueBuff_Mod, RedBuff_Slow_Mod):
    duongdan1=BlueBuff_Mod
    duongdan2=RedBuff_Slow_Mod
    with open (duongdan1, 'rb') as f:
        noidung = f.read()
        noidung = noidung.replace(b"CheckSkinIdVirtualTick", b"CheckHeroIdTick").replace(b'"skinId" value="15009"', b'"heroId" value="150"')
    with open (duongdan1,'wb') as f : f.write(noidung)
    with open (duongdan2, 'rb') as f:
        noidung = f.read()
        noidung = noidung.replace(b"CheckSkinIdVirtualTick", b"CheckHeroIdTick").replace(b'"skinId" value="15009"', b'"heroId" value="150"')
    with open (duongdan2,'wb') as f : f.write(noidung)

def QTLDKillBlue(ID_SKIN, BlueBuff_CD_Mod):
    duongdan1=BlueBuff_CD_Mod
    with open (duongdan1, 'rb') as f:
        noidung = f.read()
        noidung = noidung.replace(b"CheckSkinIdTick", b"CheckHeroIdTick").replace(b'"skinId" value="15013"', b'"heroId" value="150"').replace(b'hero_skill_effects/150_hanxin/', b'hero_skill_effects/150_hanxin/15013/')
    with open (duongdan1,'wb') as f : f.write(noidung)
    