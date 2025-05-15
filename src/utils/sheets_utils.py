import base64
import os
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account


def setup_credentials() -> str:
    """Google 인증 정보 설정
    
    환경변수에서 base64로 인코딩된 credentials를 읽어와 파일로 저장
    
    Returns:
        str: credentials 파일 경로
    """
    b64_cred = os.environ.get('GOOGLE_CREDENTIALS')
    if not b64_cred:
        raise ValueError("GOOGLE_CREDENTIALS 환경변수가 설정되지 않았습니다.")
    
    # google_upload 디렉토리가 없으면 생성
    cred_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'google_upload')
    os.makedirs(cred_dir, exist_ok=True)
    
    cred_path = os.path.join(cred_dir, 'credentials.json')
    
    # 이미 파일이 존재하면 덮어쓰지 않음
    if not os.path.exists(cred_path):
        with open(cred_path, "w") as f:
            f.write(base64.b64decode(b64_cred).decode('utf-8'))
    
    return cred_path


def get_credentials() -> service_account.Credentials:
    """Google API 인증 정보 반환
    
    Returns:
        Credentials: Google API 인증 객체
    """
    cred_path = setup_credentials()
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    return Credentials.from_service_account_file(cred_path, scopes=scopes)


def get_sheets_client(spreadsheet_id: str) -> gspread.Spreadsheet:
    """Google Sheets 클라이언트 반환
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        
    Returns:
        Spreadsheet: Google Sheets 클라이언트 객체
    """
    credentials = get_credentials()
    gc = gspread.authorize(credentials)
    return gc.open_by_key(spreadsheet_id)


def get_worksheet(spreadsheet_id: str, sheet_name: str) -> gspread.Worksheet:
    """워크시트 객체 반환
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        sheet_name: 워크시트 이름
        
    Returns:
        Worksheet: 워크시트 객체
    """
    sh = get_sheets_client(spreadsheet_id)
    return sh.worksheet(sheet_name)


def create_worksheet_if_not_exists(
    spreadsheet_id: str, 
    sheet_name: str, 
    rows: int = 100, 
    cols: int = 10,
    headers: Optional[List[str]] = None
) -> gspread.Worksheet:
    """워크시트가 없으면 생성하고 반환
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        sheet_name: 워크시트 이름
        rows: 행 수 (기본값: 100)
        cols: 열 수 (기본값: 10)
        headers: 헤더 행 데이터
        
    Returns:
        Worksheet: 워크시트 객체
    """
    sh = get_sheets_client(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=sheet_name, rows=rows, cols=cols)
        if headers:
            worksheet.append_row(headers)
    
    return worksheet


def append_row_to_sheet(
    spreadsheet_id: str, 
    sheet_name: str, 
    data: List[str],
    value_input_option: str = 'RAW'
) -> None:
    """시트에 행 추가
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        sheet_name: 워크시트 이름
        data: 추가할 행 데이터
        value_input_option: 입력 옵션 ('RAW' 또는 'USER_ENTERED')
    """
    worksheet = get_worksheet(spreadsheet_id, sheet_name)
    worksheet.append_row(data, value_input_option=value_input_option)


def get_all_values(spreadsheet_id: str, sheet_name: str, skip_headers: bool = True) -> List[List[str]]:
    """시트의 모든 값 반환
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        sheet_name: 워크시트 이름
        skip_headers: 헤더 행 제외 여부 (기본값: True)
        
    Returns:
        List[List[str]]: 시트의 모든 값
    """
    worksheet = get_worksheet(spreadsheet_id, sheet_name)
    values = worksheet.get_all_values()
    
    if skip_headers and values:
        return values[1:]
    return values


def update_cell(
    spreadsheet_id: str, 
    sheet_name: str, 
    row: int, 
    col: int, 
    value: str
) -> None:
    """특정 셀 업데이트
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        sheet_name: 워크시트 이름
        row: 행 번호 (1-based)
        col: 열 번호 (1-based)
        value: 셀에 입력할 값
    """
    worksheet = get_worksheet(spreadsheet_id, sheet_name)
    worksheet.update_cell(row, col, value)


def find_cell(spreadsheet_id: str, sheet_name: str, value: str) -> Optional[gspread.Cell]:
    """특정 값을 가진 셀 찾기
    
    Args:
        spreadsheet_id: Google Sheets 문서 ID
        sheet_name: 워크시트 이름
        value: 찾을 값
        
    Returns:
        Cell: 셀 객체 (없으면 None)
    """
    worksheet = get_worksheet(spreadsheet_id, sheet_name)
    try:
        return worksheet.find(value)
    except gspread.exceptions.CellNotFound:
        return None
