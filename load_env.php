<?php
/**
 * .env 파일 로드 (선택). 배포 시에는 서버 환경 변수를 그대로 사용.
 * - .env가 있으면 KEY=VALUE를 읽어 putenv (이미 설정된 환경 변수는 덮어쓰지 않음)
 * - 호스트(Render, Apache 등)에서 OPENAI_API_KEY를 설정했으면 그 값이 우선
 */
$envFile = (__DIR__) . DIRECTORY_SEPARATOR . '.env';
if (!is_file($envFile) || !is_readable($envFile)) {
    return;
}
$lines = @file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
if ($lines === false) {
    return;
}
foreach ($lines as $line) {
    $line = trim($line);
    if ($line === '' || $line[0] === '#') {
        continue;
    }
    $eq = strpos($line, '=');
    if ($eq === false) {
        continue;
    }
    $key = trim(substr($line, 0, $eq));
    $value = trim(substr($line, $eq + 1), " \t\"'");
    if ($key === '') {
        continue;
    }
    if (getenv($key) !== false) {
        continue;
    }
    putenv("$key=$value");
    $_ENV[$key] = $value;
}
