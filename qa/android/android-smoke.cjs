// 갤럭시(실기기 또는 Android Studio 가상기기) 크롬 점검 — 읽기 전용, 실제 전화 걸기 없음
// 사용: 1) cd 사이트폴더 && python3 -m http.server 8080
//       2) adb reverse tcp:8080 tcp:8080     (기기 안의 localhost:8080 → 이 컴퓨터)
//       3) npm i playwright && node qa/android/android-smoke.cjs [화면글자배율: 1.0 | 1.15 | 1.3]
// 주의: 이 파일은 기기가 연결된 컴퓨터에서만 돌아갑니다. 클로드 작업 환경에서는 기기가 없어 실행해 보지 못했습니다(미검증).
const { _android: android } = require('playwright');
const fs = require('fs');
const PAGES = ['index','Emergency','Health','Welfare','Centers','Jobs','Transit','Culture','All','Guide','Regions'];
(async () => {
  const scale = process.argv[2] || '1.0';
  const [device] = await android.devices();
  if (!device) { console.error('연결된 안드로이드 기기가 없어요. USB 디버깅과 adb devices를 확인하세요.'); process.exit(2); }
  console.log('기기:', device.model(), device.serial());
  await device.shell(`settings put system font_scale ${scale}`);   // 휴대폰 글자 크기 설정(보통 1.0 / 크게 1.15 / 아주 크게 1.3)
  await device.shell('am force-stop com.android.chrome');
  const ctx = await device.launchBrowser();
  const page = await ctx.newPage();
  fs.mkdirSync('qa-report/android', { recursive: true });
  const rows = []; let fail = 0;
  for (const n of PAGES) {
    await page.goto(`http://localhost:8080/${n}.html`); await page.waitForTimeout(600);
    const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, w: document.documentElement.clientWidth,
      tel: document.querySelectorAll('a[href^="tel:"]').length, small: [...document.querySelectorAll('a,button')].filter(e => { const b = e.getBoundingClientRect(); return b.width && b.height && b.height < 44; }).length }));
    const ok = r.sw - r.w <= 1;
    if (!ok) { fail++; await device.screenshot({ path: `qa-report/android/over_${n}_${scale}.png` }); }
    rows.push(`${ok ? '통과' : '실패'} | ${n} | 너비 ${r.sw}/${r.w} | 전화 ${r.tel}개 | 44px 미만 버튼 ${r.small}개`);
  }
  // 터치 확인: 첫 화면에서 '급할 때' 링크를 실제 터치로 누르기 (전화 버튼은 누르지 않음)
  await page.goto('http://localhost:8080/index.html');
  const link = page.locator('a[href="Emergency.html"]').first();
  await link.tap(); await page.waitForURL('**/Emergency.html', { timeout: 8000 }).catch(() => { fail++; rows.push('실패 | 터치로 응급 화면 이동 안 됨'); });
  // 지도 실행 확인: 응급 화면 검색 후 지도 링크의 주소만 확인(새 앱 열기까지는 사람이 눈으로 확인)
  await page.selectOption('#medicalKind', 'pharmacy'); await page.click('#medicalSearchForm button[type=submit]'); await page.waitForTimeout(800);
  const maps = await page.evaluate(() => [...document.querySelectorAll('#medicalSearchResults a[href*="map"],#medicalSearchResults a[href*="kakao"],#medicalSearchResults a[href*="naver"]')].length);
  rows.push(`${maps ? '통과' : '실패'} | 약국 지도 버튼 ${maps}개`); if (!maps) fail++;
  await device.screenshot({ path: `qa-report/android/emergency_${scale}.png` });
  await device.shell('settings put system font_scale 1.0');       // 원래대로 복구
  fs.writeFileSync('qa-report/android/report.txt', rows.join('\n') + `\n실패 ${fail}건\n`);
  console.log(rows.join('\n')); console.log('실패', fail, '건');
  await device.close(); process.exit(fail ? 1 : 0);
})();
