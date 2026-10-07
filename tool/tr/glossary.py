# -*- coding: utf-8 -*-
# 토큰/구 단위 용어집. 조합 규칙과 함께 사용.

WORD = {
# --- 재료/금속/광물 ---
"Wood":"목재","Stone":"석재","Bronze":"청동","Copper":"구리","Tin":"주석","Iron":"철","Steel":"강철",
"Rutile":"루틸","Bone":"뼈","Clay":"점토","Glass":"유리","Sandstone":"사암","Sable":"세이블",
"Nyctium":"닉티움","Void":"공허","Ore":"광석","Ingot":"주괴","Brick":"벽돌","Chunk":"덩이","Log":"통나무",
"Plank":"판자","Coal":"석탄","Crystal":"수정","Shard":"파편","Dust":"가루","Tar":"타르","Paper":"종이",
"Ink":"잉크","Water":"물","Milk":"우유","Honey":"꿀","Tallow":"수지","Hay":"건초","Wool":"양털",
"Linen":"아마포","Cloth":"천","Leather":"가죽","Hide":"가죽","Fiber":"섬유","Rope":"밧줄","Seed":"씨앗",
"Spore":"포자","Meat":"고기","Remains":"사체","Egg":"달걀","Bowl":"그릇","Bottle":"병","Bucket":"양동이",
"Pane":"판","Waste":"폐기물","Scale":"비늘","Skin":"껍질","Husk":"껍질","Flour":"밀가루","Yeast":"효모",
"Bulb":"구근","Tooth":"이빨","Fodder":"사료","Clod":"흙덩이","Sand":"모래","Dirt":"흙","Snow":"눈",
"Ice":"얼음","Ball":"덩이","Root":"뿌리","Grass":"풀","Moss":"이끼","Fern":"고사리","Tree":"나무",
"Corn":"옥수수","Rice":"쌀","Wheat":"밀",
# --- 도구/무기/방어구 ---
"Pickaxe":"곡괭이","Hatchet":"손도끼","Hammer":"망치","Chisel":"끌","Sickle":"낫","Tongs":"집게",
"Sewing Needle":"바늘","Carving Knife":"조각칼","Fishing Pole":"낚싯대","Spoon":"숟가락",
"Sword":"검","Dagger":"단검","Spear":"창","Club":"곤봉","Cudgel":"몽둥이","Mace":"철퇴","Flail":"도리깨",
"Axe":"도끼","War Axe":"전투 도끼","War Hammer":"전투 망치","Bow":"활","Crossbow":"석궁","Cross Bow":"석궁",
"Sling":"투석구","Bolas":"볼라","Dart":"다트","Atlatl":"투창기","Halberd":"미늘창","Gladius":"글라디우스",
"Khopesh":"코페시","Sagaris":"사가리스","Kukri":"쿠크리","Kris":"크리스","Scythe":"낫","Whip":"채찍",
"Chain Whip":"사슬 채찍","Staff":"지팡이","Orb":"오브","Macuahuitl":"마쿠아우이틀","Bastard Sword":"바스타드 소드",
"Long Sword":"장검","Practice Sword":"연습용 검","Practice Dagger":"연습용 단검","Pointy Stick":"뾰족한 막대",
"Buckler":"소형 방패","Kite Shield":"연 방패","Round Shield":"원형 방패","Heater Shield":"히터 실드",
"Shield":"방패","Helmet":"투구","Breastplate":"흉갑","Leggings":"각반","Boots":"장화","Cap":"모자",
"Hat":"모자","Coat":"외투","Pants":"바지","Vest":"조끼","Robe":"로브","Apron":"앞치마","Backpack":"배낭",
"Bag":"가방","Crown":"왕관","Chef's Hat":"요리사 모자",
# --- 조리/음식 ---
"Roasted":"구운","Boiled":"삶은","Toasted":"구운","Stew":"스튜","Pie":"파이","Bread":"빵","Burger":"버거",
"Sausage":"소시지","Omelette":"오믈렛","Waffles":"와플","Fries":"감자튀김","Broth":"국물","Cider":"사이다",
"Wine":"와인","Ale":"에일","Brew":"양조주","Tea":"차","Sake":"사케","Vodka":"보드카","Whiskey":"위스키",
"Potion":"물약","Trailmix":"견과 믹스","Chips":"칩","Fish":"물고기",
# --- 농작물/식물 ---
"Apple":"사과","Beetroot":"비트","Blackberry":"블랙베리","Broccoli":"브로콜리","Cabbage":"양배추",
"Carrot":"당근","Cauliflower":"콜리플라워","Celery":"셀러리","Coconut":"코코넛","Elderberry":"엘더베리",
"Gooseberry":"구스베리","Melon":"멜론","Onion":"양파","Pineapple":"파인애플","Potato":"감자",
"Pumpkin":"호박","Skyberry":"스카이베리","Sweet Potato":"고구마","Sweet Root":"단뿌리","Tomato":"토마토",
"Zucchini":"애호박","Agave":"용설란","Boletus":"그물버섯","Mushroom":"버섯","Palm":"야자","Oak":"참나무",
"Kelp":"켈프","Coral":"산호","Thumb":"엄지",
# --- 종족/고유명사 ---
"Ardyn":"아르딘(Ardyn)","Gwdir":"그위디르(Gwdir)","Tomek":"토멕(Tomek)","Traelik":"트라엘릭(Traelik)",
"Chirpen":"처픈(Chirpen)","Nequhtli":"네쿠틀리(Nequhtli)","Lopen":"로펜(Lopen)","Mirmit":"미르밋(Mirmit)",
"Gharox":"가록스(Gharox)","Gully":"걸리(Gully)","Snoot":"스누트(Snoot)","Squeaken":"스퀴큰(Squeaken)",
"Stradken":"스트라드큰(Stradken)","Tamtallen":"탐탈렌(Tamtallen)","Vytrax":"바이트락스(Vytrax)",
"Faceless":"페이스리스(Faceless)","Nightwing":"나이트윙(Nightwing)","Human":"인간","Chicken":"닭",
"Cow":"소","Deer":"사슴","Rabbit":"토끼","Rat":"쥐","Sheep":"양","Crab":"게","Owl":"올빼미","Cat":"고양이",
"Dog":"개","Kotha":"코타(Kotha)",
# --- 일반 ---
"Light":"경량","Medium":"중형","Heavy":"중량","Large":"대형","Small":"소형","Plant":"식물",
"Ancient":"고대","Makeshift":"임시","Draw Well":"두레우물","Bottled":"병에 담은","Glow":"발광",
"Animal":"동물","Food":"음식","Health":"체력","Youth":"젊음","Arcane":"비전","Desert":"사막",
"Forest":"숲","Shimmer":"어른거림","Emerald":"에메랄드","Opal":"오팔","Sapphire":"사파이어",
"Amber":"앰버","Sunrise":"일출","Seabreeze":"바닷바람","Deep":"깊은","Shadow":"그림자","Twilight":"황혼",
"Night":"밤","Ghost":"유령","Blood":"피","Purified":"정제된","From":"—",
}

# 전체 문자열 그대로 치환 (우선 적용)
PHRASE = {}
