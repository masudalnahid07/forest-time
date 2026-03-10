customColorPalette = [
        {
            'color': 'hsl(4, 90%, 58%)',
            'label': 'Red'
        },
        {
            'color': 'hsl(340, 82%, 52%)',
            'label': 'Pink'
        },
        {
            'color': 'hsl(291, 64%, 42%)',
            'label': 'Purple'
        },
        {
            'color': 'hsl(262, 52%, 47%)',
            'label': 'Deep Purple'
        },
        {
            'color': 'hsl(231, 48%, 48%)',
            'label': 'Indigo'
        },
        {
            'color': 'hsl(207, 90%, 54%)',
            'label': 'Blue'
        },
    ]

CKEDITOR_5_CUSTOM_CSS = 'path_to.css' # optional
CKEDITOR_5_FILE_STORAGE = "path_to_storage.CustomStorage" # optional
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': {
            'items': [
                'heading', '|', 'bold', 'italic', 'link',
                'bulletedList', 'numberedList', 'blockQuote', 
                'imageUpload',  # শুধুমাত্র imageUpload রাখা হলো
                # নতুন প্লাগইন
                'WordCount', 'Markdown', 'PageBreak', 'HtmlEmbed', 
                'RemoveFormat', 'MediaEmbed', 'PasteFromOffice', 
                'Alignment', 'CodeBlock', 'Autoformat'
            ],
        }
    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3','heading4',  # heading4 যুক্ত
            '|',
            'bulletedList', 'numberedList',
            '|',
            'blockQuote',
            '|',
            'PageBreak', 'Autoformat', 'Alignment'
        ],
        'toolbar': {
            'items': [
                'heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 
                'link', 'underline', 'strikethrough', 'code', 'subscript', 
                'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 
                'imageUpload', 'bulletedList', 'numberedList', 'todoList', '|',  
                'blockQuote', '|',
                'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 
                'mediaEmbed', 'removeFormat', 'insertTable',
                # নতুন প্লাগইন
                'WordCount', 'Markdown', 'PageBreak', 'HtmlEmbed', 
                'PasteFromOffice', 'Alignment', 'Autoformat'
            ],
            'shouldNotGroupWhenFull': 'true'
        },
        'image': {
            'toolbar': [
                'imageTextAlternative',  # alt tag
                '|', 
                'imageStyle:alignLeft', 'imageStyle:alignRight', 
                'imageStyle:alignCenter', 'imageStyle:side', '|',
                'MediaEmbed', 'RemoveFormat'  # duplicate ImageInsert সরানো হয়েছে
            ],
            'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter']
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
                'tableProperties', 'tableCellProperties',
                'RemoveFormat', 'CodeBlock'
            ],
            'tableProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            },
            'tableCellProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            }
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
                {'model': 'heading4', 'view': 'h4', 'title': 'Heading 4', 'class': 'ck-heading_heading4'}  # নতুন
            ]
        }
    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        }
    }
}
