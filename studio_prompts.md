# Studio 붙여넣기용 프롬프트 — 嫁に「老眼鏡なんてみっともない」と言われた姑の、その後

## 0단계: 인물 사진 4장 만들기 (Nano Banana / 이미지 모델)

Studio 채팅에서 이미지 모델을 고르고, 아래를 하나씩 붙여넣으세요. 마음에 드는 사진을 **인물 이름으로 저장**해 두세요 (kazuko.png 등).

### 和子（姑・68歳） → `kazuko.png`
```
Photorealistic portrait of a 68-year-old Japanese woman, kind but dignified face, short neat gray-black bob, light makeup, beige knit cardigan over a cream blouse, thin gold reading glasses hanging on a fine chain around her neck. Upper body, facing camera, soft restaurant background, natural window light, 9:16 vertical.
```

### 麗奈（嫁・38歳） → `rena.png`
```
Photorealistic portrait of a 38-year-old Japanese woman, fashionable and slightly haughty expression, long wavy brown hair, polished makeup, white silk blouse, designer handbag strap on shoulder. Upper body, facing camera, soft restaurant background, natural window light, 9:16 vertical.
```

### 健太（息子・40歳） → `kenta.png`
```
Photorealistic portrait of a 40-year-old Japanese man, mild timid expression, short black hair, navy sweater over white shirt. Upper body, soft restaurant background, 9:16 vertical.
```

### 蒼太（孫・7歳） → `sota.png`
```
Photorealistic portrait of a cheerful 7-year-old Japanese boy, round face, short bowl haircut, striped T-shirt, a small birthday paper crown on his head. Upper body, soft restaurant background, 9:16 vertical.
```

## 1단계: 장면 10개 만들기 (Gemini Omni 1.1 Flash)

각 장면마다: **새 채팅 → 모델 gemini-omni-1.1-flash → 적힌 인물 사진 첨부 → 프롬프트 붙여넣기 → 생성 → 다운로드**. 파일 이름은 `s01.mp4`처럼 장면 번호로 저장하세요.

### s01 — 첨부할 사진: `rena.png`, `kazuko.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: rena = 麗奈（嫁・38歳）, kazuko = 和子（姑・68歳）. Hook shot. Close-up at a family restaurant table. The older woman (kazuko) has just put on her thin gold reading glasses to read the menu. The younger woman (rena) suddenly snatches the menu out of her hands, glaring, and says sharply in Japanese: 「お義母さん、それ人前でかけないでくださいよ。みっともない」. Kazuko freezes, shocked. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** お義母さん ／ それ人前で ／ かけないで ／ ください！ ／ みっともない

### s02 — 첨부할 사진: `kazuko.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: kazuko = 和子（姑・68歳）. Medium shot of kazuko sitting still, the reading glasses half lowered, her face stiff with embarrassment. Diners at nearby tables glance over. Silence, only restaurant ambience. A birthday cake with candles sits on the table. 9:16 vertical video, 5 seconds.
```
**자막 (Vrew에 한 덩어리씩):** 孫の誕生日 ／ 家族で来た ／ レストランで

### s03 — 첨부할 사진: `rena.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: rena = 麗奈（嫁・38歳）. Rena leans in and says in a lowered but cutting voice in Japanese: 「年寄りくさいのよ。あっちに私のママ友も来てるんだから」, then tilts her head toward a nearby table where three stylish women in their late thirties are sitting and watching. 9:16 vertical video, 7 seconds.
```
**자막 (Vrew에 한 덩어리씩):** 年寄りくさいのよ ／ あっちに ／ 私のママ友も ／ 来てるんだから

### s04 — 첨부할 사진: `kazuko.png`, `kenta.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: kazuko = 和子（姑・68歳）, kenta = 健太（息子・40歳）. Kazuko quietly takes off the reading glasses, folds them and slips them into a small brown leather case, eyes lowered. Beside her, her son kenta stares down at his plate and says nothing. Melancholic, quiet mood. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** 息子は ／ 何も言わなかった

### s05 — 첨부할 사진: `rena.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: rena = 麗奈（嫁・38歳）. Time skip to the end of the meal. A waiter places the bill on the table. Rena picks up the long printed receipt, squints hard, and slowly holds it farther and farther away from her face, frowning. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** そして ／ お会計

### s06 — 첨부할 사진: `rena.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: rena = 麗奈（嫁・38歳）. Rena, flustered, mutters in Japanese: 「…え、これ何円？字が小さすぎて…」. At the next table her three mom friends notice, exchange looks and smirk behind their hands. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** え…これ何円？ ／ 字が ／ 小さすぎて…

### s07 — 첨부할 사진: `kazuko.png`, `rena.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: kazuko = 和子（姑・68歳）, rena = 麗奈（嫁・38歳）. Kazuko calmly opens the brown leather case, takes out her thin gold reading glasses and holds them out to rena with a gentle, composed smile. She says softly in Japanese: 「貸してあげる。似合うわよ」. 9:16 vertical video, 7 seconds.
```
**자막 (Vrew에 한 덩어리씩):** 貸してあげる ／ 似合うわよ

### s08 — 첨부할 사진: `sota.png`, `rena.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: sota = 蒼太（孫・7歳）, rena = 麗奈（嫁・38歳）. Rena's face turns red. The little boy sota, wearing a paper birthday crown, laughs innocently and says loudly in Japanese: 「ママもおばあちゃんとおそろいだね！」. The mom friends at the next table burst into giggles. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** ママも ／ おばあちゃんと ／ おそろいだね！

### s09 — 첨부할 사진: `rena.png`, `kazuko.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: rena = 麗奈（嫁・38歳）, kazuko = 和子（姑・68歳）. Rena sheepishly puts on the gold reading glasses, reads the receipt, and mumbles in Japanese, not making eye contact: 「…ありがとうございます」. Kazuko sips her green tea, satisfied. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** …ありがとう ／ ございます

### s10 — 첨부할 사진: `kazuko.png`
```
Photorealistic cinematic Japanese TV drama, shot on a 35mm lens, shallow depth of field, warm natural indoor lighting, realistic skin texture, vertical 9:16 framing. All dialogue is spoken in natural Japanese. No on-screen text, no subtitles, no watermarks. Setting: A bright, upscale family restaurant in Tokyo at lunchtime, wooden tables, other diners in the background. Characters in the reference images: kazuko = 和子（姑・68歳）. Slow push-in close-up on kazuko's face as she smiles warmly and serenely, soft golden window light behind her. No dialogue, gentle ambience. 9:16 vertical video, 6 seconds.
```
**자막 (Vrew에 한 덩어리씩):** 老いを笑う人も ／ いつか必ず ／ 同じ道を通る

## 2단계: Vrew로 편집

1. Vrew에서 새 프로젝트 → `s01.mp4`~`s10.mp4`를 순서대로 불러오기
2. 각 장면의 **자막**을 위 「자막」 덩어리대로 입력 (화면 가운데, 큰 글씨, 흰 글자+검은 테두리)
3. 「！」「？」가 있는 덩어리는 노란색으로
4. 마지막에 3초 검은 화면 + `あなたなら、
どうしますか？` / 작게 `※本内容は、実際のエピソードを基に再構成したものです。`
5. 내보내기 → 유튜브 업로드 시 **「변경되거나 합성된 콘텐츠」 → 예** 선택
