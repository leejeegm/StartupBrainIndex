<?php
error_reporting(0);
ini_set('display_errors', 0);
ob_start();

header('Content-Type: application/json; charset=utf-8');

try {
    $input = json_decode(file_get_contents('php://input'), true);
    $imageId = $input['imageId'] ?? '';

    if (empty($imageId)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '이미지 ID가 없습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    // 메타데이터 파일 찾기
    $metadataFile = null;
    $files = glob('uploads/' . $imageId . '*_metadata.json');

    if (empty($files)) {
        // 이미지 ID로 직접 찾기
        $pattern = 'uploads/*_metadata.json';
        $allFiles = glob($pattern);
        
        if ($allFiles !== false) {
            foreach ($allFiles as $file) {
                if (!file_exists($file) || !is_readable($file)) {
                    continue;
                }
                
                $fileContent = @file_get_contents($file);
                if ($fileContent === false) {
                    continue;
                }
                
                $metadata = @json_decode($fileContent, true);
                if ($metadata && isset($metadata['image_id']) && $metadata['image_id'] === $imageId) {
                    $metadataFile = $file;
                    break;
                }
            }
        }
    } else {
        $metadataFile = $files[0];
    }

    if (!$metadataFile || !file_exists($metadataFile)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '메타데이터 파일을 찾을 수 없습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    $fileContent = @file_get_contents($metadataFile);
    if ($fileContent === false) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '메타데이터 파일을 읽을 수 없습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }
    
    $metadata = @json_decode($fileContent, true);
    if (!$metadata || !is_array($metadata)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '메타데이터 형식이 올바르지 않습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }
    
    $imageFile = 'uploads/' . ($metadata['filename'] ?? '');

    if (!file_exists($imageFile)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '이미지 파일을 찾을 수 없습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    // 설명 파일 읽기
    $imageIdFromMeta = $metadata['image_id'] ?? $imageId;
    $descriptionFile = 'uploads/' . $imageIdFromMeta . '_description.txt';
    $description = '';
    if (file_exists($descriptionFile)) {
        $description = @file_get_contents($descriptionFile);
        if ($description === false) {
            $description = '';
        }
    }

    // 텍스트 파일 읽기
    $textFile = 'uploads/' . $imageIdFromMeta . '_text.txt';
    $text = $metadata['text'] ?? '';
    if (file_exists($textFile)) {
        $textContent = @file_get_contents($textFile);
        if ($textContent !== false) {
            $text = $textContent;
        }
    }

    ob_clean();
    echo json_encode([
        'success' => true,
        'imageUrl' => $imageFile,
        'imageId' => $imageIdFromMeta,
        'text' => $text,
        'description' => $description,
        'title' => $metadata['title'] ?? ''
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
} catch (Exception $e) {
    ob_clean();
    echo json_encode([
        'success' => false,
        'message' => '이미지 불러오기 중 오류가 발생했습니다: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}

ob_end_flush();
?>
