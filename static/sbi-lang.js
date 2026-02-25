/**
 * SBI 공통 언어 설정. localStorage sbi_lang (ko/en).
 * 회원가입 시 국적 선택에 따라 로그인부터 해당 언어 적용.
 */
(function() {
  var KEY = 'sbi_lang';
  window.getSbiLang = function() {
    try {
      var v = localStorage.getItem(KEY);
      return (v && String(v).toLowerCase().trim() === 'en') ? 'en' : 'ko';
    } catch (e) {
      return 'ko';
    }
  };
  window.setSbiLang = function(lang) {
    try {
      var v = (lang && String(lang).toLowerCase().trim()) === 'en' ? 'en' : 'ko';
      localStorage.setItem(KEY, v);
    } catch (e) {}
  };
  /** 국적 값 → 언어 코드. 대한민국 → ko, 그 외 → en (추후 일본/중국 등 확장 가능) */
  window.langFromNationality = function(nationality) {
    if (!nationality || typeof nationality !== 'string') return 'ko';
    var n = nationality.trim();
    if (n === '대한민국') return 'ko';
    if (n === 'Japan' || n === '日本') return 'en'; // 일본어 미지원 시 en
    if (n === 'China' || n === '中国') return 'en';
    return 'en';
  };
})();
