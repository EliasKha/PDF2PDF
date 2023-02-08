import PyPDF2
import pdfplumber
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import pandas as pd

##extracts the text sucessfully
def extract_text_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(open(pdf_file, "rb"))
    page = pdf_reader.pages[0]

    tables = []
    text = []
    text_mode = True
    table = []
    for line in page.extract_text().split("\n"):
        if line.startswith("\t"):
            if text_mode:
                text_mode = False
            table.append(line.strip().split("\t"))
        else:
            if not text_mode:
                text_mode = True
                tables.append(table)
                table = []
            text.append(line)

    return  text


#Extracts the tables sucessfully
def extract_tables_from_pdf(pdf_file):
    tables = []
    text = []
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        extracted_tables = page.extract_tables()
        if extracted_tables:
            for table in extracted_tables:
                tables.append(pd.DataFrame(table))
        else:
            for i, char in enumerate(page.chars):
                if char["text"] == " " and char["top"] - page.chars[i-1]["top"] > 10:
                    text.append(page.extract_text(char["bottom"], page.chars[i-1]["top"]).strip())

    return tables


def mix_tables_and_pdf(tables,text):
	result = []
	for line in text:
		iterator=1
		for table in tables:
			value_test = 0
			for i in range(len(table.T)):
				if table[i][0] in line:
					value_test+=1
			if value_test == len(table.T):
				result.append(table)
				break
			elif iterator == len(tables):
				result.append(line)
				break
			else:
				iterator+=1
	return result


def turn_strings_of_data_into_a_list(datalist):
	interm_datalist = []
	#separate in the list elements separated by '/'
	for element in datalist:
		if type(element) == str:
			element = element.split('/')
			if len(element) == 2:
				if element[1][0]== ' ':
					element[1]= element[1][1:]
				element[1] = '/'+element[1]
			for item in element:
				interm_datalist.append(item)
		else:
			interm_datalist.append(element)	
	
	datalist = interm_datalist
	interm_datalist = []
	for element in datalist:
		if type(element) == str:
			element = element.split(':')
			if len(element) == 2:
				element = pd.DataFrame(element)
				interm_datalist.append(element)
			else:
				for item in element:
					interm_datalist.append(item)
		else:
			interm_datalist.append(element)	

	return interm_datalist


def keep_the_tables_only(datalist):
	interm_datalist = []
	for element in datalist:
		if type(element) != str:
			interm_datalist.append(element)			
	return interm_datalist


def update_templateb_with_templatea_data(data_templateA,data_templateB):
	for elementB_position in range(len(data_templateB)):
		if type(data_templateB[elementB_position]) != str:
			for elementA in data_templateA:
				if data_templateB[elementB_position].T[0].equals(elementA.T[0]) :
					data_templateB[elementB_position] = elementA
	return data_templateB


def give_original_format_of_template(final_data_templateB):
	new_final_data_templateB = []
	for element in final_data_templateB:
		if type(element) == str:
			new_final_data_templateB.append(element)
		else:
			if len(element) == 2 and len(element.T) == 1:
				sub_element = element[0][0] + ':' +element[0][1]
				new_final_data_templateB.append(sub_element)
			else:
				new_final_data_templateB.append(element)

	final_data_templateB = new_final_data_templateB
	new_final_data_templateB = []
	for element in final_data_templateB:
		if type(element) != str:
			new_final_data_templateB.append(element)
		else:
			if '/' in element:
				new_final_data_templateB[-1] = new_final_data_templateB[-1] + element
			else:
				new_final_data_templateB.append(element)

	return new_final_data_templateB
		


def generate_pdf(data, file_name, margin=0.5*inch, space_between_elements=0.1*inch):
    doc = SimpleDocTemplate(file_name, pagesize=pagesizes.letter, leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin)
    
    elements = []
    for item in data:
        if isinstance(item, str):
            elements.append(Paragraph(item, getSampleStyleSheet()['Normal']))
            elements.append(Paragraph("", getSampleStyleSheet()['Normal']))
        elif isinstance(item, pd.DataFrame):
            max_col_width = [0] * len(item.columns)
            for i in range(len(item.columns)):
                for j in range(len(item.index)):
                    if len(str(item.iloc[j, i])) > max_col_width[i]:
                        max_col_width[i] = len(str(item.iloc[j, i]))
            table = Table(item.values.tolist(), colWidths=[(doc.width - 2 * margin) * (width / sum(max_col_width)) for width in max_col_width])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), 'white'),
                ('GRID', (0, 0), (-1, -1), 1, "black"),
                ('BORDER', (0, 0), (-1, -1), 1, "black"),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT')
            ]))
            elements.append(table)
            elements.append(Paragraph("", getSampleStyleSheet()['Normal']))
        
        elements.append(Paragraph("", ParagraphStyle(name='Normal', spaceAfter=space_between_elements)))
    
    doc.build(elements)










##get the data from TemplateA
pdf_file = 'TemplateA.pdf'
tables = extract_tables_from_pdf(pdf_file)
text = extract_text_pdf(pdf_file)
result = mix_tables_and_pdf(tables,text)
result2 = turn_strings_of_data_into_a_list(result)
data_templateA = keep_the_tables_only(result2)




##get data from TemplateB
pdf_file = 'TemplateB.pdf'
tables = extract_tables_from_pdf(pdf_file)
text = extract_text_pdf(pdf_file)
result = mix_tables_and_pdf(tables,text)
data_templateB = turn_strings_of_data_into_a_list(result)


final_data_templateB = update_templateb_with_templatea_data(data_templateA,data_templateB)
new_final_data_templateB = give_original_format_of_template(final_data_templateB)	


generate_pdf(new_final_data_templateB, 'output.pdf')
