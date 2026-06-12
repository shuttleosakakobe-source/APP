function doPost(e) {
  var reply = { "status": "error", "message": "No data received" };
  
  try {
    var jsonString = e.postData.contents;
    var data = JSON.parse(jsonString);
    
    // スプレッドシートID
    var targetSpreadsheetId = "1cPgQ3Ej3P7JZPaxprFQnbnDkCatQ15lEHyF9C9tMgZ4";
    var ss = SpreadsheetApp.openById(targetSpreadsheetId);
    
    var now = new Date();
    // 🗓️ A列に勝手に入る日付の形（yyyy/MM/dd 形式）
    var todayStr = Utilities.formatDate(now, "JST", "yyyy/MM/dd");
    var timeStr = Utilities.formatDate(now, "JST", "HH:mm");
    var cleanToday = todayStr.replace(/[-/]/g, "");

    // -------------------------------------------------------------
    // 【機能A】業務チェックリスト処理 (GET_CHECKLIST または COMPLETE_TASK)
    // -------------------------------------------------------------
    if (data.status === "GET_CHECKLIST" || data.status === "COMPLETE_TASK") {
      
      var targetSheet = ss.getSheetByName("業務チェックリスト");
      if (!targetSheet) {
        return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": "「業務チェックリスト」シートが見つかりません。" })).setMimeType(ContentService.MimeType.JSON);
      }
      
      // 1行目の結合されたタスク名を正しく解析する
      var lastCol = Math.max(targetSheet.getLastColumn(), 3);
      var firstRowValues = targetSheet.getRange(1, 1, 1, lastCol).getValues()[0];
      
      var taskHeaders = [];
      var currentTask = "";
      for (var c = 0; c < firstRowValues.length; c++) {
        var val = firstRowValues[c].toString().trim();
        if (val !== "") {
          currentTask = val;
        }
        taskHeaders.push(currentTask);
      }
      
      // --- データ取得 (GET_CHECKLIST) ---
      if (data.status === "GET_CHECKLIST") {
        var lastRow = targetSheet.getLastRow();
        var completedTasks = [];
        
        if (lastRow >= 3) { 
          var rows = targetSheet.getDataRange().getValues();
          var requestDateStr = data.date ? data.date.replace(/[-/]/g, "") : cleanToday;
          
          for (var i = 2; i < rows.length; i++) {
            var rowDate = rows[i][0];
            if (!rowDate) continue;
            
            var formattedRowDate = "";
            if (rowDate instanceof Date) {
              formattedRowDate = Utilities.formatDate(rowDate, "JST", "yyyyMMdd");
            } else {
              formattedRowDate = rowDate.toString().split(" ")[0].replace(/[-/]/g, "");
            }
            
            if (formattedRowDate === requestDateStr) {
              for (var colIdx = 1; colIdx < lastCol; colIdx++) {
                var taskName = taskHeaders[colIdx];
                var cellVal = rows[i][colIdx];
                var colNameLabel = targetSheet.getRange(2, colIdx + 1).getValue().toString().trim();
                
                if (colNameLabel === "タイム" && cellVal && cellVal.toString().trim() !== "") {
                  if (taskName && taskName !== "日付") {
                    completedTasks.push(taskName);
                  }
                }
              }
            }
          }
        }
        var uniqueTasks = completedTasks.filter(function(x, i, self) { return self.indexOf(x) === i; });
        reply = { "status": "success", "completed": uniqueTasks };
        return ContentService.createTextOutput(JSON.stringify(reply)).setMimeType(ContentService.MimeType.JSON);
      }
      
      // --- タスク完了記録 (COMPLETE_TASK) ---
      if (data.status === "COMPLETE_TASK") {
        var userName = data.name || "不明";
        var taskName = (data.task || "").toString().trim();
        
        // 対象タスクの「タイム」が書き込まれるべき正確な列番号を探す
        var targetTimeColIdx = -1;
        for (var hIdx = 1; hIdx < taskHeaders.length; hIdx++) {
          if (taskHeaders[hIdx] === taskName) {
            var label = targetSheet.getRange(2, hIdx + 1).getValue().toString().trim();
            if (label === "タイム") {
              targetTimeColIdx = hIdx + 1;
              break;
            }
          }
        }
        
        if (targetTimeColIdx <= 0) {
          return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": "指定されたタスク「" + taskName + "」の列が見つかりません。" })).setMimeType(ContentService.MimeType.JSON);
        }
        
        var lastRow = targetSheet.getLastRow();
        var targetRowIdx = -1;
        
        // すでに「今日の日付」の行が作られているか探す
        if (lastRow >= 3) {
          var rows = targetSheet.getDataRange().getValues();
          for (var i = 2; i < rows.length; i++) {
            var rowDate = rows[i][0];
            if (!rowDate) continue;
            
            var formattedRowDate = "";
            if (rowDate instanceof Date) {
              formattedRowDate = Utilities.formatDate(rowDate, "JST", "yyyyMMdd");
            } else {
              formattedRowDate = rowDate.toString().split(" ")[0].replace(/[-/]/g, "");
            }
            
            if (formattedRowDate === cleanToday) {
              targetRowIdx = i + 1; // 今日の行を発見
              break;
            }
          }
        }
        
        if (targetRowIdx !== -1) {
          // 【今日2回目以降のボタン押下】すでにある行の対象列に追記
          targetSheet.getRange(targetRowIdx, targetTimeColIdx).setValue(timeStr).setNumberFormat("@");
          targetSheet.getRange(targetRowIdx, targetTimeColIdx + 1).setValue(userName).setNumberFormat("@");
        } else {
          // 【今日初めてのボタン押下】一番下の空白行に新しく日付行を作成
          var nextRow = Math.max(lastRow + 1, 3);
          
          // ✨ A列に「今日の日付」を自動セット
          var dateCell = targetSheet.getRange(nextRow, 1);
          dateCell.setValue(todayStr);
          dateCell.setNumberFormat("yyyy/MM/dd");
          
          // 対応する列にタイムと名前をセット
          targetSheet.getRange(nextRow, targetTimeColIdx).setValue(timeStr).setNumberFormat("@");
          targetSheet.getRange(nextRow, targetTimeColIdx + 1).setValue(userName).setNumberFormat("@");
          
          // 全体に綺麗な格子罫線を引く
          targetSheet.getRange(nextRow, 1, 1, lastCol).setBorder(true, true, true, true, true, true, "#e0e0e0", SpreadsheetApp.BorderStyle.SOLID);
        }
        
        reply = { "status": "success", "message": "タスク完了を記録しました。" };
        return ContentService.createTextOutput(JSON.stringify(reply)).setMimeType(ContentService.MimeType.JSON);
      }
    }
    
    // -------------------------------------------------------------
    // 【機能B】タイムカード（勤怠・所在打刻）処理 (TIMECARD)
    // -------------------------------------------------------------
    if (data.status === "TIMECARD") {
      var timecardSheet = getSheetByGid(ss, "1985339649");
      if (!timecardSheet) {
        timecardSheet = ss.getSheetByName("タイムカード") || ss.getSheets()[0];
      }
      
      var timestamp = new Date();
      var dateStr = Utilities.formatDate(timestamp, "JST", "yyyy/MM/dd");
      var timeSecStr = Utilities.formatDate(timestamp, "JST", "HH:mm:ss");
      var currentStatus = data.timecard_status || "打刻";
      
      timecardSheet.appendRow([
        dateStr,
        data.code || "",
        data.name || "",
        currentStatus, 
        timeSecStr
      ]);
      
      reply = { "status": "success", "message": "Attendance data saved successfully" };
      return ContentService.createTextOutput(JSON.stringify(reply)).setMimeType(ContentService.MimeType.JSON);
    }
    
  } catch (error) {
    reply = { "status": "error", "message": error.toString() };
  }
  
  return ContentService.createTextOutput(JSON.stringify(reply)).setMimeType(ContentService.MimeType.JSON);
}

function getSheetByGid(ss, gid) {
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getSheetId().toString() === gid.toString()) {
      return sheets[i];
    }
  }
  return null;
}
