<?php
require_once __DIR__ . '/load_env.php';
require_once 'openai_api.php';

header('Content-Type: application/json');

// 로컬: .env 의 OPENAI_API_KEY 또는 시스템 환경변수 사용
$apiKey = getenv('OPENAI_API_KEY') ?: ($_ENV['OPENAI_API_KEY'] ?? '');

$input = json_decode(file_get_contents('php://input'), true);
$text = $input['text'] ?? '';

if (empty($text)) {
    echo json_encode(['success' => false, 'message' => '텍스트가 입력되지 않았습니다.']);
    exit;
}

// AI를 통해 텍스트를 이미지화 요약 설명 생성
$result = analyzeTextFile($text, $apiKey);

if ($result['error']) {
    echo json_encode(['success' => false, 'message' => '설명 생성 실패: ' . $result['message']]);
    exit;
}

$description = $result['data']['choices'][0]['message']['content'] ?? '';

echo json_encode([
    'success' => true,
    'description' => $description
]);
?>
