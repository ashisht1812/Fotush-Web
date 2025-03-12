import pandas as pd
import yaml
from reportlab.platypus.tables import TableStyle
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Image
from reportlab.platypus.flowables import PageBreak, Spacer, HRFlowable, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from jinja2 import Environment, FileSystemLoader
from PyPDF2 import PdfReader, PdfWriter
import pdfkit
import io
import re
import datetime
from datetime import datetime
import os
import tempfile
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportEngine:
    def __init__(self, config, scenarios, db_cursor, env):
        self.config = config
        self.common = self.config["common"]
        self.reports = self.config["reports"]
        self.env = env
        self.scenarios = scenarios
        self.db_cursor = db_cursor
        self.bookmarks = {}  # Changed to dict for easier page number lookup
        self.flag_manager = FlagManager(config["flag_rules"])
        
        # Set up page size and margins
        self.page_size = landscape(A4)
        self.page_width, self.page_height = self.page_size
        self.left_margin = inch * 0.75
        self.right_margin = inch * 0.75
        self.top_margin = inch * 0.75
        self.bottom_margin = inch * 0.75

        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # Initialize previous business line and sub team name
        self.previous_business_line = None
        self.previous_sub_team_name = None

    def _setup_styles(self):
        """Set up document styles with modern, professional formatting."""
        # Get the base stylesheet
        self.styles = getSampleStyleSheet()
        
        # Modify existing styles instead of creating new ones where possible
        self.styles['Title'].textColor = colors.HexColor("#2C3E50")  # Modern dark blue
        self.styles['Title'].fontSize = 20
        self.styles['Title'].leading = 24
        self.styles['Title'].spaceBefore = 30
        self.styles['Title'].spaceAfter = 20
        self.styles['Title'].alignment = TA_LEFT

        self.styles['Heading1'].textColor = colors.HexColor("#2C3E50")
        self.styles['Heading1'].fontSize = 16
        self.styles['Heading1'].leading = 20
        self.styles['Heading1'].spaceBefore = 15
        self.styles['Heading1'].spaceAfter = 10

        self.styles['Heading2'].textColor = colors.HexColor("#34495E")
        self.styles['Heading2'].fontSize = 14
        self.styles['Heading2'].leading = 18
        self.styles['Heading2'].spaceBefore = 12
        self.styles['Heading2'].spaceAfter = 8

        self.styles['BodyText'].textColor = colors.HexColor("#2C3E50")
        self.styles['BodyText'].fontSize = 10
        self.styles['BodyText'].leading = 14
        self.styles['BodyText'].spaceBefore = 6
        self.styles['BodyText'].spaceAfter = 6

        # Add custom styles that don't exist in the base stylesheet
        self.styles.add(ParagraphStyle(
            name="TOCTitle",
            parent=self.styles['Title'],
            fontSize=20,
            leading=24,
            spaceBefore=30,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#2C3E50")
        ))

        self.styles.add(ParagraphStyle(
            name="TOCHeading1",
            parent=self.styles['Heading1'],
            fontSize=12,
            leading=16,
            spaceBefore=8,
            spaceAfter=4,
            leftIndent=0,
            textColor=colors.HexColor("#34495E")
        ))

        self.styles.add(ParagraphStyle(
            name="TOCHeading2",
            parent=self.styles['Heading2'],
            fontSize=11,
            leading=14,
            spaceBefore=4,
            spaceAfter=4,
            leftIndent=20,
            textColor=colors.HexColor("#7F8C8D")
        ))

        self.styles.add(ParagraphStyle(
            name="FootnoteHeading",
            parent=self.styles['BodyText'],
            fontSize=9,
            leading=12,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#34495E")
        ))

        self.styles.add(ParagraphStyle(
            name="FootnoteText",
            parent=self.styles['BodyText'],
            fontSize=8,
            leading=10,
            spaceBefore=2,
            spaceAfter=2,
            leftIndent=20,
            textColor=colors.HexColor("#7F8C8D")
        ))

        self.styles.add(ParagraphStyle(
            name="Highlighted",
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor("#E74C3C")
        ))

        self.styles.add(ParagraphStyle(
            name="HighlightedBackground",
            parent=self.styles['BodyText'],
            fontSize=12,
            backColor=colors.HexColor("#FFF9C4"),
            textColor=colors.HexColor("#2C3E50")
        ))

        self.styles.add(ParagraphStyle(
            name="NormalStyle",
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2C3E50")
        ))

    def build_table_of_contents(self):
        """Build a modern, professional table of contents with enhanced styling."""
        elements = []
        
        # Add TOC title with modern styling
        toc_title = Paragraph("Table of Contents", self.styles["TOCTitle"])
        elements.append(toc_title)
        
        # Add horizontal line with modern styling
        elements.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#E0E0E0"),  # Light gray
            spaceBefore=5,
            spaceAfter=25,
            lineCap=1
        ))
        
        # Get sections from configuration
        sections = self.reports.get("sections", [])
        section_counter = 1
        
        for section in sections:
            title = section.get("title", section.get("section_name", ""))
            subsections = section.get("subsections", [])
            page_num = self.bookmarks.get(title, 1)
            
            # Create bookmark key
            bookmark_key = f"section_{section_counter}"
            
            # Format main section with modern styling
            dots = "." * (60 - len(f"{section_counter}. {title}") - len(str(page_num)))
            toc_text = f'<link href="#{bookmark_key}"><b>{section_counter}. {title}</b>{dots}{page_num}</link>'
            elements.append(Paragraph(toc_text, self.styles["TOCHeading1"]))
            
            # Store bookmark for this section
            self.bookmarks[bookmark_key] = page_num
            
            # Format subsections with modern styling
            if subsections:
                for sub_idx, subsection in enumerate(subsections, 1):
                    sub_title = subsection.get("title", "")
                    sub_page = self.bookmarks.get(f"{title}:{sub_title}", page_num)
                    
                    # Create bookmark key for subsection
                    sub_bookmark_key = f"section_{section_counter}_{sub_idx}"
                    
                    sub_dots = "." * (55 - len(f"{section_counter}.{sub_idx} {sub_title}") - len(str(sub_page)))
                    sub_text = f'<link href="#{sub_bookmark_key}">{section_counter}.{sub_idx} {sub_title}{sub_dots}{sub_page}</link>'
                    elements.append(Paragraph(sub_text, self.styles["TOCHeading2"]))
                    
                    # Store bookmark for this subsection
                    self.bookmarks[sub_bookmark_key] = sub_page
            
            section_counter += 1
        
        elements.append(PageBreak())
        return elements

    def on_page(self, canvas, doc):
        """Add professional header and footer to each page with modern styling."""
        canvas.saveState()
        
        # Get current page number
        page_num = doc.page
        
        # Add header (except on first page)
        if page_num > 1:
            # Header text
            canvas.setFont('Helvetica-Bold', 11)
            header_text = self.reports.get("title", "Report")
            canvas.setFillColor(colors.HexColor("#2C3E50"))  # Modern dark blue
            canvas.drawCentredString(self.page_width/2, self.page_height - 20, header_text)
            
            # Header line
            canvas.setStrokeColor(colors.HexColor("#E0E0E0"))  # Light gray
            canvas.setLineWidth(0.5)
            canvas.line(self.left_margin, self.page_height - 30,
                       self.page_width - self.right_margin, self.page_height - 30)
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#7F8C8D"))  # Modern gray
        
        # Footer line
        canvas.setStrokeColor(colors.HexColor("#E0E0E0"))  # Light gray
        canvas.setLineWidth(0.5)
        canvas.line(self.left_margin, 30,
                   self.page_width - self.right_margin, 30)
        
        # Page number with modern styling
        page_text = f"Page {page_num}"
        canvas.drawString(self.left_margin, 15, page_text)
        
        # Date with modern styling
        date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
        canvas.drawCentredString(self.page_width/2, 15, date_text)
        
        # Report name with modern styling
        footer_text = self.reports.get("name", "Report")
        canvas.drawRightString(self.page_width - self.right_margin, 15, footer_text)
        
        # Add bookmarks for the current page
        for bookmark_key, bookmark_page in self.bookmarks.items():
            if bookmark_page == page_num:
                canvas.bookmarkPage(bookmark_key)
        
        canvas.restoreState()

    def prepare_table_data(self, report_column_info, dataframe, multi_level_headers=None):
        """Prepare table data with support for multi-level headers and group colors."""
        custom_style = self.get_custom_style()
        table_data = []
        header_rows = {}
        
        # If multi_level_headers is None, initialize it as an empty list
        if multi_level_headers is None:
            multi_level_headers = []
        
        # First, organize columns by groups
        groups = {}
        for col_info in report_column_info:
            group = col_info.get("group")
            if group:
                if group not in groups:
                    groups[group] = []
                groups[group].append(col_info)
        
        # If we have groups, create a group header row
        if groups:
            group_row = []
            current_group = None
            group_span = 0
            group_spans = []  # Store spans for styling
            
            for col_info in report_column_info:
                group = col_info.get("group")
                if group != current_group:
                    if current_group and group_span > 0:
                        cell = Paragraph(f"<b>{current_group}</b>", custom_style)
                        group_row.append(cell)
                        group_spans.append((len(group_row)-1, group_span))
                    current_group = group
                    group_span = 1
                else:
                    group_span += 1
            
            # Add the last group
            if current_group and group_span > 0:
                cell = Paragraph(f"<b>{current_group}</b>", custom_style)
                group_row.append(cell)
                group_spans.append((len(group_row)-1, group_span))
            
            # Add the group row to table data
            if group_row:  # Only add if there are actual groups
                table_data.append(group_row)
                header_rows[0] = {"row_type": "group", "spans": group_spans}
        
        # Create column header row
        header_row = []
        for col_info in report_column_info:
            header_text = col_info.get("display_name", col_info.get("name", col_info.get("header", "")))
            header_cell = Paragraph(f"<b>{header_text}</b>", custom_style)
            header_row.append(header_cell)
        
        # Add the header row to table data
        table_data.append(header_row)
        header_rows[len(table_data) - 1] = {
            "row_type": "header",
            "levels": [col_info.get("level", 1) for col_info in report_column_info]
        }
        
        # Add data rows
        data_rows = []
        if dataframe is not None and not dataframe.empty:
            for _, row in dataframe.iterrows():
                data_row = []
                for col_info in report_column_info:
                    column_name = col_info.get("name", col_info.get("column", ""))
                    if column_name in row:
                        cell_value = row[column_name]
                        if pd.isna(cell_value):
                            cell_value = ""
                        elif isinstance(cell_value, (float, np.floating)):
                            cell_value = f"{cell_value:.2f}"
                        cell = Paragraph(str(cell_value), custom_style)
                        data_row.append(cell)
                    else:
                        # Handle missing columns gracefully
                        data_row.append(Paragraph("", custom_style))
                data_rows.append(data_row)
        
        # Create table style commands
        style_commands = []
        
        # Basic styling
        style_commands.extend([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
        ])
        
        # Header styling
        header_offset = 0
        if groups and 0 in header_rows:
            header_offset = 1
            group_spans = header_rows[0]["spans"]
            for group_idx, span in group_spans:
                style_commands.extend([
                    ('BACKGROUND', (group_idx, 0), (group_idx + span - 1, 0), colors.HexColor("#2C3E50")),
                    ('TEXTCOLOR', (group_idx, 0), (group_idx + span - 1, 0), colors.white),
                    ('SPAN', (group_idx, 0), (group_idx + span - 1, 0)),
                    ('ALIGN', (group_idx, 0), (group_idx + span - 1, 0), 'CENTER'),
                    ('FONTNAME', (group_idx, 0), (group_idx + span - 1, 0), 'Helvetica-Bold'),
                ])
        
        # Column header styling
        for col_idx in range(len(header_row)):
            style_commands.extend([
                ('BACKGROUND', (col_idx, header_offset), (col_idx, header_offset), colors.HexColor("#34495E")),
                ('TEXTCOLOR', (col_idx, header_offset), (col_idx, header_offset), colors.white),
                ('ALIGN', (col_idx, header_offset), (col_idx, header_offset), 'CENTER'),
                ('FONTNAME', (col_idx, header_offset), (col_idx, header_offset), 'Helvetica-Bold'),
            ])
        
        # Alternating row colors
        for row_idx in range(header_offset + 1, header_offset + 1 + len(data_rows), 2):
            style_commands.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor("#F8F9FA")))
        
        return data_rows, style_commands

    def create_table_style(self, style_config, data=None):
        """Create a TableStyle with modern, professional formatting."""
        # Modern color palette
        header_colors = style_config.get("header_colors", {
            "level1": "#2C3E50",  # Dark blue
            "level2": "#34495E",  # Medium blue
            "level3": "#446CB3"   # Light blue
        })
        group_colors = style_config.get("group_colors", {})
        
        # Base table style with modern aesthetics
        table_style = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),  # Lighter grid lines
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#2C3E50")),  # Stronger header bottom border
        ]
        
        # Get header rows information
        header_rows = style_config.get("header_rows", {})
        
        # Style group headers (first row)
        if data and 0 in header_rows and header_rows[0]["row_type"] == "group":
            group_spans = header_rows[0]["spans"]
            for group_idx, span in group_spans:
                group_name = data[0][group_idx].getPlainText().strip("<b></b>")
                group_color = colors.HexColor(group_colors.get(group_name, header_colors["level1"]))
                table_style.extend([
                    ('BACKGROUND', (group_idx, 0), (group_idx + span - 1, 0), group_color),
                    ('TEXTCOLOR', (group_idx, 0), (group_idx + span - 1, 0), colors.white),
                    ('SPAN', (group_idx, 0), (group_idx + span - 1, 0)),
                    ('ALIGN', (group_idx, 0), (group_idx + span - 1, 0), 'CENTER'),
                    ('FONTNAME', (group_idx, 0), (group_idx + span - 1, 0), 'Helvetica-Bold'),
                ])
        
        # Style column headers (second row)
        if 1 in header_rows and header_rows[1]["row_type"] == "header":
            levels = header_rows[1]["levels"]
            for col_idx, level in enumerate(levels):
                header_color = colors.HexColor(header_colors.get(f"level{level}", header_colors["level1"]))
                table_style.extend([
                    ('BACKGROUND', (col_idx, 1), (col_idx, 1), header_color),
                    ('TEXTCOLOR', (col_idx, 1), (col_idx, 1), colors.white),
                    ('ALIGN', (col_idx, 1), (col_idx, 1), 'CENTER'),
                    ('FONTNAME', (col_idx, 1), (col_idx, 1), 'Helvetica-Bold'),
                ])
        
        # Add subtle alternating row colors for better readability
        alt_background = colors.HexColor("#F8F9FA")  # Very light gray
        if data:
            for row in range(2, len(data), 2):
                table_style.append(('BACKGROUND', (0, row), (-1, row), alt_background))
        
        return TableStyle(table_style)

    def get_custom_style(self):
        """Get a custom style from the stylesheet."""
        # Return the NormalStyle directly if it exists
        if "NormalStyle" in self.styles:
            return self.styles["NormalStyle"]
        
        # If NormalStyle doesn't exist, return BodyText as a fallback
        if "BodyText" in self.styles:
            return self.styles["BodyText"]
            
        # Last resort, return Normal style
        return self.styles["Normal"]

    def render_front_page(self, effective_date):
        """ Render the first page using Jinja2 and convert it to PDF. """
        env = Environment(loader=FileSystemLoader("./templates"))
        template = env.get_template("front_page.html")
        if isinstance(effective_date, str):
            effective_date = datetime.strptime(effective_date, "%Y-%m-%d").strftime("%B %d, %Y")
        html_content = template.render({"config": self.config['front_page'], "effective_date": effective_date})
        temp_file_name = "temp_html.html"

        with open(temp_file_name, "w") as file:
            file.write(html_content)

        executable_path = "/ms/dist/fsf/PROJ/wkhtmltopdf-0.12.6/bin/wkhtmltopdf"
        pdf_config = pdfkit.configuration(wkhtmltopdf=executable_path)
        pdf_bytes = pdfkit.from_file(temp_file_name, False, configuration=pdf_config,
                                     options={"enable-local-file-access": "", "page-size": "A4", "orientation": "Landscape"})
        return pdf_bytes

    def generate_report_pages(self):
        """Generate report pages using ReportLab with bookmark support."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        
        # Add sections with bookmarks
        section_counter = 1
        for section in self.reports.get("sections", []):
            title = section.get("title", section.get("section_name", ""))
            bookmark_key = f"section_{section_counter}"
            
            # Add section title with bookmark
            section_title = Paragraph(title, self.styles["Heading1"])
            section_title.bookmarkName = bookmark_key
            elements.append(section_title)
            
            # Add subsections with bookmarks if they exist
            if section.get("subsections"):
                for sub_idx, subsection in enumerate(section["subsections"], 1):
                    sub_title = subsection.get("title", "")
                    sub_bookmark_key = f"section_{section_counter}_{sub_idx}"
                    
                    # Add subsection title with bookmark
                    sub_title_elem = Paragraph(sub_title, self.styles["Heading2"])
                    sub_title_elem.bookmarkName = sub_bookmark_key
                    elements.append(sub_title_elem)
            
            section_counter += 1
        
        elements.append(PageBreak())
        doc.build(elements, onFirstPage=self.on_page, onLaterPages=self.on_page)
        return buffer.getvalue()

    def combine_pdfs(self, pdf_front, pdf_report):
        output_pdf = PdfWriter()
        front_pdf_reader = PdfReader(io.BytesIO(pdf_front))
        report_pdf_reader = PdfReader(io.BytesIO(pdf_report))

        # Add the front page
        output_pdf.add_page(front_pdf_reader.pages[0])

        # Add remaining report pages
        for page in report_pdf_reader.pages:
            output_pdf.add_page(page)

        with open("combined_report.pdf", "wb") as outfile:
            output_pdf.write(outfile)

    def run_report(self):
        """Run the report generation process using the generate_pdf_report method."""
        effective_date = self.common.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Load sample data for demonstration
        try:
            # Try to load sample data from CSV if available
            sample_data_path = "sample_data.csv"
            if os.path.exists(sample_data_path):
                df = pd.read_csv(sample_data_path)
                print(f"Loaded sample data with {len(df)} rows")
            else:
                # Create dummy data if no CSV is available
                print("No sample data found, creating dummy data")
                df = pd.DataFrame({
                    'INVESTMENT_TEAM_NAME': ['Team A', 'Team A', 'Team B', 'Team B'],
                    'INVESTMENT_SUB_TEAM_NAME': ['Sub A1', 'Sub A2', 'Sub B1', 'Sub B2'],
                    'MARKET_VALUE': [1000.0, 2000.0, 1500.0, 2500.0]
                })
        except Exception as e:
            print(f"Error loading data: {e}")
            # Create minimal dummy data in case of error
            df = pd.DataFrame({
                'INVESTMENT_TEAM_NAME': ['Team A'],
                'INVESTMENT_SUB_TEAM_NAME': ['Sub A1'],
                'MARKET_VALUE': [1000.0]
            })
        
        # Generate the report using the enhanced method
        report_file, flagged_items = self.generate_pdf_report(df, effective_date)
        
        print(f"Report generated successfully: {report_file}")
        if flagged_items:
            print(f"Found {len(flagged_items)} flagged items in the report")
        
        return report_file

    def generate_pdf_report(self, df, effective_date):
        """ Generate a PDF report based on the report configurations. """

        filename = self.reports['filename']

        # Convert effective_date to datetime if it's a string
        if isinstance(effective_date, str):
            effective_date = datetime.strptime(effective_date, "%m/%d/%Y")

        formatted_effective_date = effective_date.strftime("%Y-%m-%d")
        file_name_with_date = f"{filename}_{formatted_effective_date}.pdf"

        if self.env == 'qa':
            report_location = self.reports['report_location_qa']
        elif self.env == 'prod':
            report_location = self.reports['report_location_prod']
        else:
            report_location = '.'

        file_name_with_date = report_location + file_name_with_date

        buffer = io.BytesIO()
        pagesize = landscape(A2)
        margins = [5, 5, 5, 5]

        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            rightMargin=margins[1],
            leftMargin=margins[3],
            topMargin=margins[0],
            bottomMargin=margins[2],
        )

        on_page_callback = lambda canvas, doc: self.on_page(canvas, doc)
        elements = []

        flagged_items_summary = []

        group_colors = {
            'Group1': '#DCDCDC',
            'Group2': '#C8E6C9',
            'Group3': '#BBDEFB',
            'Group4': '#A9A9A9',
            'Group5': '#9E9E9E'
        }

        for section in self.reports['topics']:
            title = section['title']
            content = section['content']
            self.register_bookmark(title)
            elements.append(Paragraph(title, self.styles['Heading1']))
            elements.append(Paragraph(f"{content}", self.styles['TOCHeading2']))
            elements.append(PageBreak())

            for section in self.reports['topics']:
                elements.append(Paragraph(section['title'], self.styles['Heading1']))
                elements.append(Paragraph(section['content'], self.styles['Heading2']))
                elements.append(Spacer(1, 12))

                for table_config in section['sections']:
                    db_filter_criteria = None
                    filtered_df = {}

                    if db_filter_criteria:
                        filter_criteria = db_filter_criteria
                    else:
                        section = table_config.get('section')
                        filter_criteria = section.get('filter_criteria', {}) if section else {}

                    if not filter_criteria:
                        print("No filter criteria available. Skipping filtering step.")
                        filtered_df = df.copy()
                    else:
                        filtered_df = df.copy()
                        for column, condition in filter_criteria.items():
                            filtered_df = self.apply_filter(filtered_df, column, condition)

                    # Get column information
                    report_columns_info = table_config['report_columns_info']
                    
                    # Create custom style for text
                    custom_style = self.get_custom_style()
                    
                    # Create table data structure
                    table_data = []
                    
                    # Create header row
                    header_row = []
                    for col_info in report_columns_info:
                        header_text = col_info.get('header', col_info.get('display_name', col_info.get('name', '')))
                        header_cell = Paragraph(f"<b>{header_text}</b>", custom_style)
                        header_row.append(header_cell)
                    
                    # Add header row to table data
                    table_data.append(header_row)
                    
                    # Add data rows
                    if filtered_df is not None and not filtered_df.empty:
                        for _, row in filtered_df.iterrows():
                            data_row = []
                            for col_info in report_columns_info:
                                column_name = col_info.get('name', col_info.get('column', ''))
                                if column_name in row:
                                    cell_value = row[column_name]
                                    if pd.isna(cell_value):
                                        cell_value = ""
                                    elif isinstance(cell_value, (float, np.floating)):
                                        cell_value = f"{cell_value:.2f}"
                                    cell = Paragraph(str(cell_value), custom_style)
                                    data_row.append(cell)
                                else:
                                    # Handle missing columns gracefully
                                    data_row.append(Paragraph("", custom_style))
                            table_data.append(data_row)
                    
                    # Process flag data
                    flagged_data = []
                    for rule_key, rule in self.config['flag_rules'].items():
                        conditions = rule['conditions']
                        severity = rule['severity']
                        color = rule['color']
                        text_color = rule['text_color']
                        column = rule['field']

                        if filtered_df is not None:
                            for index, row in filtered_df.iterrows():
                                if self.flag_manager.evaluate_conditions(row, conditions):
                                    flagged_data.append({
                                        'index': index,
                                        'column': column,
                                        'color': color,
                                        'severity': severity,
                                        'text_color': text_color
                                    })

                    self.flag_manager.save_flagged_data(flagged_data, 'flag_records')
                    
                    # Calculate grand total
                    grand_total = filtered_df['MARKET_VALUE'].sum() if filtered_df is not None and 'MARKET_VALUE' in filtered_df.columns else 0
                    
                    # Add grand total row
                    grand_total_row = [Paragraph('<b>Grand Total</b>', custom_style)]
                    # Add empty cells for middle columns
                    for _ in range(len(header_row) - 2):
                        grand_total_row.append(Paragraph('', custom_style))
                    # Add the total value in the last column
                    grand_total_row.append(Paragraph(f"{round(grand_total, 2)}", custom_style))
                    table_data.append(grand_total_row)
                    
                    # Add aggregated team data if available
                    if filtered_df is not None and 'INVESTMENT_TEAM_NAME' in filtered_df.columns and 'INVESTMENT_SUB_TEAM_NAME' in filtered_df.columns:
                        try:
                            aggregated_values_team = filtered_df.groupby(['INVESTMENT_TEAM_NAME', 'INVESTMENT_SUB_TEAM_NAME'])["MARKET_VALUE"].sum().reset_index()
                            
                            for _, team_row in aggregated_values_team.iterrows():
                                investment_team_name = team_row['INVESTMENT_TEAM_NAME']
                                investment_sub_team_name = team_row['INVESTMENT_SUB_TEAM_NAME']
                                aggregated_value = team_row['MARKET_VALUE']
                                
                                formatted_row = [
                                    Paragraph(f"<b>{investment_team_name}</b>", custom_style),
                                    Paragraph(f"{investment_sub_team_name}", custom_style)
                                ]
                                # Add empty cells for middle columns if needed
                                for _ in range(len(header_row) - 3):
                                    formatted_row.append(Paragraph('', custom_style))
                                # Add the aggregated value in the last column
                                formatted_row.append(Paragraph(f"{aggregated_value:.2f}", custom_style))
                                table_data.append(formatted_row)
                        except Exception as e:
                            print(f"Error aggregating team data: {e}")
                    
                    # Create table style
                    header_styles = [
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center align header
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),  # Header background
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Header padding
                        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),  # Grid lines
                    ]
                    
                    # Add alternating row colors
                    for row_idx in range(1, len(table_data), 2):
                        header_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor("#F8F9FA")))
                    
                    # Create the table style
                    table_style = TableStyle(header_styles)
                    
                    # Create the table
                    table = Table(table_data)
                    table.setStyle(table_style)
                    
                    elements.append(table)
                    elements.append(PageBreak())

        toc_elements = self.build_table_of_contents()
        elements.extend(toc_elements)

        init_doc = SimpleDocTemplate(
            filename,
            pagesize=pagesize,
            rightMargin=margins[1],
            leftMargin=margins[3],
            topMargin=margins[0],
            bottomMargin=margins[2],
        )

        init_doc.build(toc_elements + elements, onFirstPage=on_page_callback, onLaterPages=on_page_callback)

        pdf_front_page = self.render_front_page(formatted_effective_date)

        final_pdf = PdfWriter()

        front_pdf_reader = PdfReader(io.BytesIO(pdf_front_page))
        report_pdf_reader = PdfReader(buffer)

        final_pdf.add_page(front_pdf_reader.pages[0])

        for page in report_pdf_reader.pages:
            final_pdf.add_page(page)

        with open(file_name_with_date, 'wb') as outfile:
            final_pdf.write(outfile)

        return file_name_with_date, flagged_items_summary

    def register_bookmark(self, title):
        """Register a bookmark for the TOC."""
        self.bookmarks[title] = len(self.bookmarks) + 1

    def apply_filter(self, df, column, condition):
        """ Apply filters based on the condition. """
        if isinstance(condition, list):
            # Handle list of values for inclusion
            return df[df[column].isin(condition)]
        elif isinstance(condition, str):
            # Check for numeric comparison
            match = re.match(r'([<>]=?)\s*(\d+(\.\d+)?)', condition)
            if match:
                operator, value = match.groups()[0:2]
                value = float(value)  # Convert value to float for comparison
                if operator == '>':
                    return df[df[column] > value]
                elif operator == '<':
                    return df[df[column] < value]
                elif operator == '>=':
                    return df[df[column] >= value]
                elif operator == '<=':
                    return df[df[column] <= value]
                elif operator == '==':
                    return df[df[column] == value]
            else:
                # Direct equality for string and non-list values
                return df[df[column] == condition]
        return df

# ... [Keep your FlagManager class and other classes unchanged] ...

if __name__ == "__main__":
    # Example configuration setup
    config = {
        "common": {"effective_date": "2025-03-02"},
        "reports": {
            "filename": "sample_report",
            "report_location_qa": "/qa_reports/",
            "report_location_prod": "/prod_reports/",
            "flag_rules": {}
        }
    }
    
    # Load sample data
    try:
        # Try to load sample data from CSV if available
        sample_data_path = "sample_data.csv"
        if os.path.exists(sample_data_path):
            df = pd.read_csv(sample_data_path)
            print(f"Loaded sample data with {len(df)} rows")
        else:
            # Create dummy data if no CSV is available
            print("No sample data found, creating dummy data")
            df = pd.DataFrame({
                'INVESTMENT_TEAM_NAME': ['Team A', 'Team A', 'Team B', 'Team B'],
                'INVESTMENT_SUB_TEAM_NAME': ['Sub A1', 'Sub A2', 'Sub B1', 'Sub B2'],
                'MARKET_VALUE': [1000.0, 2000.0, 1500.0, 2500.0]
            })
    except Exception as e:
        print(f"Error loading data: {e}")
        # Create minimal dummy data in case of error
        df = pd.DataFrame({
            'INVESTMENT_TEAM_NAME': ['Team A'],
            'INVESTMENT_SUB_TEAM_NAME': ['Sub A1'],
            'MARKET_VALUE': [1000.0]
        })
    
    # Get effective date from config
    effective_date = config["common"]["effective_date"]
    
    # Initialize the report engine
    scenarios = {}
    db_cursor = None
    env = "qa"
    
    # Create the report engine
    engine = ReportEngine(config, scenarios, db_cursor, env)
    
    # Generate the report by directly calling generate_pdf_report
    report_file, flagged_items = engine.generate_pdf_report(df, effective_date)
    
    print(f"Report generated successfully: {report_file}")
    if flagged_items:
        print(f"Found {len(flagged_items)} flagged items in the report") 