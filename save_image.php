<?php
error_reporting(0);
ini_set('display_errors', 0);
ob_start();

header('Content-Type: application/json; charset=utf-8');

try {
    $input = json_decode(file_get_contents('php://input'), true);
    $imageId = $input['imageId'] ?? '';
    $text = $input['text'] ?? '';
    $imageUrl = $input['imageUrl'] ?? '';

    // uploads 디렉토리 확인 및 생성
    if (!file_exists('uploads')) {
        if (!mkdir('uploads', 0777, true)) {
            ob_clean();
            echo json_encode(['success' => false, 'message' => 'uploads 디렉토리를 생성할 수 없습니다.'], JSON_UNESCAPED_UNICODE);
            ob_end_flush();
            exit;
        }
    }

    // 이미지 ID가 없으면 새로 생성
    if (empty($imageId)) {
        if (empty($imageUrl)) {
            ob_clean();
            echo json_encode(['success' => false, 'message' => '이미지 ID 또는 이미지 URL이 필요합니다.'], JSON_UNESCAPED_UNICODE);
            ob_end_flush();
            exit;
        }
        
        // 이미지 URL에서 이미지 다운로드
        $imageData = @file_get_contents($imageUrl);
        if ($imageData === false) {
            ob_clean();
            echo json_encode(['success' => false, 'message' => '이미지를 다운로드할 수 없습니다.'], JSON_UNESCAPED_UNICODE);
            ob_end_flush();
            exit;
        }
        
        $imageId = 'img_' . time() . '_' . uniqid();
        $filename = $imageId . '.png';
        $filepath = 'uploads/' . $filename;
        
        if (!file_put_contents($filepath, $imageData)) {
            ob_clean();
            echo json_encode(['success' => false, 'message' => '이미지 파일 저장에 실패했습니다.'], JSON_UNESCAPED_UNICODE);
            ob_end_flush();
            exit;
        }
        
        // 새 메타데이터 생성
        $metadata = [
            'image_id' => $imageId,
            'filename' => $filename,
            'text' => $text,
            'saved' => true,
            'saved_at' => date('Y-m-d H:i:s'),
            'created_at' => date('Y-m-d H:i:s')
        ];
        
        $metadataFile = 'uploads/' . $imageId . '_metadata.json';
    } else {
        // 기존 메타데이터 파일 찾기
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
                    
                    $fileMetadata = @json_decode($fileContent, true);
                    if ($fileMetadata && isset($fileMetadata['image_id']) && $fileMetadata['image_id'] === $imageId) {
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
            echo json_encode(['success' => false, 'message' => '메타데이터를 읽을 수 없습니다.'], JSON_UNESCAPED_UNICODE);
            ob_end_flush();
            exit;
        }
        
        // 저장 정보 추가/업데이트
        $metadata['saved'] = true;
        $metadata['saved_at'] = date('Y-m-d H:i:s');
        if (!empty($text)) {
            $metadata['text'] = $text;
        }
    }

    // 메타데이터 파일 저장
    $jsonData = json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    if ($jsonData === false) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '메타데이터 JSON 인코딩 실패.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    if (!file_put_contents($metadataFile, $jsonData)) {
        ob_clean();
        echo json_encode(['success' => false, 'message' => '메타데이터 파일 저장에 실패했습니다.'], JSON_UNESCAPED_UNICODE);
        ob_end_flush();
        exit;
    }

    // 텍스트 파일 저장/업데이트
    if (!empty($text)) {
        $textFile = 'uploads/' . $imageId . '_text.txt';
        if (!file_put_contents($textFile, $text)) {
            // 텍스트 파일 저장 실패는 경고만 하고 계속 진행
            error_log("텍스트 파일 저장 실패: " . $textFile);
        }
    }

    ob_clean();
    echo json_encode([
        'success' => true, 
        'message' => '이미지가 저장되었습니다.',
        'imageId' => $imageId
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
} catch (Exception $e) {
    ob_clean();
    echo json_encode([
        'success' => false,
        'message' => '이미지 저장 중 오류가 발생했습니다: ' . $e->getMessage()
    ], JSON_UNESCAPED_UNICODE);
}

ob_end_flush();
?>
