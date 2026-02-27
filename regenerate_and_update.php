<?php
require_once 'openai_api.php';

header('Content-Type: application/json');

$apiKey = getenv('OPENAI_API_KEY') ?: '';

$input = json_decode(file_get_contents('php://input'), true);
$imageId = $input['imageId'] ?? '';
$text = $input['text'] ?? '';

if (empty($imageId)) {
    echo json_encode(['success' => false, 'message' => '이미지 ID가 없습니다.']);
    exit;
}

if (empty($text)) {
    echo json_encode(['success' => false, 'message' => '텍스트가 입력되지 않았습니다.']);
    exit;
}

// 기존 메타데이터 파일 찾기
$metadataFile = null;
$files = glob('uploads/' . $imageId . '*_metadata.json');

if (empty($files)) {
    $pattern = 'uploads/*_metadata.json';
    $allFiles = glob($pattern);
    
    foreach ($allFiles as $file) {
        $fileMetadata = @json_decode(file_get_contents($file), true);
        if ($fileMetadata && isset($fileMetadata['image_id']) && $fileMetadata['image_id'] === $imageId) {
            $metadataFile = $file;
            break;
        }
    }
} else {
    $metadataFile = $files[0];
}

if (!$metadataFile || !file_exists($metadataFile)) {
    echo json_encode(['success' => false, 'message' => '메타데이터 파일을 찾을 수 없습니다.']);
    exit;
}

$metadata = json_decode(file_get_contents($metadataFile), true);
if (!$metadata) {
    echo json_encode(['success' => false, 'message' => '메타데이터를 읽을 수 없습니다.']);
    exit;
}

// AI를 통해 텍스트를 이미지 생성용 프롬프트로 변환
$analysisResult = analyzeTextFile($text, $apiKey);

if ($analysisResult['error']) {
    echo json_encode(['success' => false, 'message' => '프롬프트 생성 실패: ' . $analysisResult['message']]);
    exit;
}

$prompt = $analysisResult['data']['choices'][0]['message']['content'] ?? $text;

// DALL-E로 새 이미지 생성
$imageResult = generateImageWithDALLE($prompt, $apiKey);

if ($imageResult['error']) {
    echo json_encode(['success' => false, 'message' => '이미지 생성 실패: ' . $imageResult['message']]);
    exit;
}

$imageUrl = $imageResult['data']['data'][0]['url'] ?? null;

if (!$imageUrl) {
    echo json_encode(['success' => false, 'message' => '이미지 URL을 가져올 수 없습니다.']);
    exit;
}

// 새 이미지 다운로드
$imageData = @file_get_contents($imageUrl);
if ($imageData === false) {
    echo json_encode(['success' => false, 'message' => '이미지를 다운로드할 수 없습니다.']);
    exit;
}

// 기존 이미지 파일 경로
$oldImageFile = 'uploads/' . $metadata['filename'];
$imageFile = $oldImageFile;

// 이미지 파일 업데이트
if (!file_put_contents($imageFile, $imageData)) {
    echo json_encode(['success' => false, 'message' => '이미지 파일 저장에 실패했습니다.']);
    exit;
}

// 이미지 설명 생성
$description = '';
try {
    $imageBase64 = base64_encode($imageData);
    $descriptionResult = getImageDescription($imageBase64, $apiKey);
    
    if (!$descriptionResult['error']) {
        $description = $descriptionResult['data']['choices'][0]['message']['content'] ?? '';
    }
} catch (Exception $e) {
    error_log('이미지 설명 생성 오류: ' . $e->getMessage());
    $description = $metadata['description'] ?? '';
}

// 메타데이터 업데이트
$metadata['text'] = $text;
$metadata['prompt'] = $prompt;
$metadata['description'] = $description;
$metadata['updated_at'] = date('Y-m-d H:i:s');
$metadata['regenerated_at'] = date('Y-m-d H:i:s');

// 메타데이터 파일 저장
$jsonData = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
if ($jsonData === false) {
    echo json_encode(['success' => false, 'message' => '메타데이터 JSON 인코딩 실패.']);
    exit;
}

if (!file_put_contents($metadataFile, $jsonData)) {
    echo json_encode(['success' => false, 'message' => '메타데이터 파일 저장에 실패했습니다.']);
    exit;
}

// 텍스트 및 설명 파일 업데이트
file_put_contents('uploads/' . $imageId . '_text.txt', $text);
file_put_contents('uploads/' . $imageId . '_description.txt', $description);

echo json_encode([
    'success' => true,
    'imageUrl' => $imageFile,
    'imageId' => $imageId,
    'description' => $description,
    'message' => '이미지가 재생성되었습니다.'
]);
?>
