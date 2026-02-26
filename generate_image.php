<?php
error_reporting(0);
ini_set('display_errors', 0);
ob_start();

require_once __DIR__ . '/load_env.php';
require_once __DIR__ . '/openai_api.php';

header('Content-Type: application/json; charset=utf-8');

$apiKey = getenv('OPENAI_API_KEY') ?: '';
if ($apiKey === '') {
    ob_clean();
    echo json_encode(['success' => false, 'message' => 'OPENAI_API_KEY가 설정되지 않았습니다. .env 또는 서버 환경 변수를 확인하세요.'], JSON_UNESCAPED_UNICODE);
    ob_end_flush();
    exit;
}

try {
    $input = json_decode(file_get_contents('php://input'), true);
    $text = $input['text'] ?? '';

    if (empty($text)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '텍스트가 입력되지 않았습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

// AI를 통해 텍스트를 이미지 생성용 프롬프트로 변환
$prompt = $text; // 기본값으로 원본 텍스트 사용
$analysisResult = analyzeTextFile($text, $apiKey);

if (!$analysisResult['error']) {
    $generatedPrompt = $analysisResult['data']['choices'][0]['message']['content'] ?? '';
    if (!empty($generatedPrompt)) {
        $prompt = $generatedPrompt;
    }
} else {
    // 프롬프트 생성 실패 시 원본 텍스트 사용
    error_log('프롬프트 생성 실패, 원본 텍스트 사용: ' . $analysisResult['message']);
}

// DALL-E로 이미지 생성
$imageResult = generateImageWithDALLE($prompt, $apiKey);

    if ($imageResult['error']) {
        $errorMsg = '이미지 생성 실패: ' . $imageResult['message'];
        if (isset($imageResult['http_code'])) {
            $errorMsg .= ' (HTTP ' . $imageResult['http_code'] . ')';
        }
        ob_clean();
        echo json_encode(['success' => false, 'message' => $errorMsg], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    // 응답 데이터 확인
    if (!isset($imageResult['data']) || !isset($imageResult['data']['data']) || !is_array($imageResult['data']['data'])) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '이미지 생성 응답 형식이 올바르지 않습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    $imageUrl = $imageResult['data']['data'][0]['url'] ?? null;

    if (!$imageUrl) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '이미지 URL을 가져올 수 없습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

// 이미지 다운로드 (재시도 로직 포함)
$imageData = false;
$maxRetries = 3;
$retryCount = 0;

while ($retryCount < $maxRetries && $imageData === false) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $imageUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    $imageData = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlError = curl_error($ch);
    curl_close($ch);
    
    if ($imageData === false || $httpCode !== 200) {
        $retryCount++;
        if ($retryCount < $maxRetries) {
            sleep(1); // 1초 대기 후 재시도
        }
    }
}

    if ($imageData === false || empty($imageData)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '이미지를 다운로드할 수 없습니다. (재시도 ' . $maxRetries . '회 실패)'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    $imageId = 'img_' . time() . '_' . uniqid();
    $filename = $imageId . '.png';
    $filepath = 'uploads/' . $filename;

    if (!file_exists('uploads')) {
        if (!mkdir('uploads', 0777, true)) {
            ob_clean();
            echo json_encode(['success' => false, 'message' => 'uploads 디렉토리를 생성할 수 없습니다.'], JSON_UNESCAPED_UNICODE);
            ob_end_flush();
            exit;
        }
    }

    if (!file_put_contents($filepath, $imageData)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '이미지 파일 저장에 실패했습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

// 이미지 설명 생성 (이미지가 생성되었으므로 base64로 변환하여 설명 요청)
$description = '';
try {
    // 이미지 크기가 너무 크면 설명 생성을 건너뛰기 (API 제한)
    $imageSize = strlen($imageData);
    if ($imageSize > 20 * 1024 * 1024) { // 20MB 이상이면 건너뛰기
        $description = '이미지가 너무 커서 자동 설명 생성을 건너뛰었습니다.';
    } else {
        $imageBase64 = base64_encode($imageData);
        $descriptionResult = getImageDescription($imageBase64, $apiKey);
        
        if (!$descriptionResult['error']) {
            $description = $descriptionResult['data']['choices'][0]['message']['content'] ?? '';
        } else {
            error_log('이미지 설명 생성 실패: ' . $descriptionResult['message']);
            $description = '이미지 설명 생성에 실패했습니다.';
        }
    }
} catch (Exception $e) {
    // 설명 생성 실패해도 이미지는 반환
    error_log('이미지 설명 생성 오류: ' . $e->getMessage());
    $description = '이미지 설명을 생성하는 중 오류가 발생했습니다.';
}

// 제목 추천 생성
$suggestedTitles = [];
try {
    $titleResult = suggestImageTitles($text, $description, $apiKey);
    
    if (!$titleResult['error']) {
        $titleText = $titleResult['data']['choices'][0]['message']['content'] ?? '';
        // 줄바꿈으로 구분된 제목들을 배열로 변환
        $titles = array_filter(array_map('trim', explode("\n", $titleText)));
        $suggestedTitles = array_slice($titles, 0, 3); // 최대 3개만
    } else {
        error_log('제목 추천 실패: ' . $titleResult['message']);
    }
} catch (Exception $e) {
    error_log('제목 추천 오류: ' . $e->getMessage());
}

// 제목이 없으면 기본 제목 생성
if (empty($suggestedTitles)) {
    $suggestedTitles = [
        '생성된 이미지',
        '새로운 이미지',
        '이미지 ' . date('Y-m-d')
    ];
}

// 메타데이터 저장
$metadata = [
    'image_id' => $imageId,
    'filename' => $filename,
    'text' => $text,
    'prompt' => $prompt,
    'description' => $description,
    'created_at' => date('Y-m-d H:i:s')
];

file_put_contents('uploads/' . $imageId . '_metadata.json', json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
file_put_contents('uploads/' . $imageId . '_text.txt', $text);
file_put_contents('uploads/' . $imageId . '_description.txt', $description);

// 자동 저장 (생성 즉시 저장)
$metadata['saved'] = true;
$metadata['saved_at'] = date('Y-m-d H:i:s');

    // 메타데이터 파일 업데이트
    file_put_contents('uploads/' . $imageId . '_metadata.json', json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));

    ob_clean();
    echo json_encode([
        'success' => true,
        'imageUrl' => $filepath,
        'imageId' => $imageId,
        'description' => $description,
        'suggestedTitles' => $suggestedTitles,
        'message' => '이미지가 생성되고 자동으로 저장되었습니다.'
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
} catch (Exception $e) {
    ob_clean();
    echo json_encode([
        'success' => false,
        'message' => '이미지 생성 중 오류가 발생했습니다: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}

ob_end_flush();
?>
