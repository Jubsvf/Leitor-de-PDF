import os
import io
import re
import json
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()


CATEGORIAS_SINAIS = {
    "MANUTENÇÃO E OPERAÇÃO": [
        "GRAXA", "ÓLEO", "OLEO", "DIESEL", "LUBRIFICANTE", "PEÇAS", "PECAS",
        "PARAFUSO", "ANEL", "BUCHA", "ROLAMENTO", "PNEU", "FILTRO", "CORREIA",
        "FERRAMENTA", "MÁQUINAS AGRÍCOLAS", "MAQUINAS AGRICOLAS", "ESTOPA",
        "PANO PARA LIMPEZA", "LIMPADOR", "VEDAÇÃO", "RETENTOR", "BATERIA",
        "SOLDA", "MANGUEIRA", "DISCO DE CORTE", "CABO", "PORCA", "ARRUELA"
    ],
    "INSUMOS AGRÍCOLAS": [
        "SEMENTE", "SEMENTES", "FERTILIZANTE", "FERTILIZANTES", "ADUBO",
        "DEFENSIVO", "DEFENSIVOS", "HERBICIDA", "FUNGICIDA", "INSETICIDA",
        "CORRETIVO", "CALCÁRIO", "CALCARIO", "GESSO AGRÍCOLA", "INOCULANTE",
        "NUTRIÇÃO FOLIAR"
    ],
    "RECURSOS HUMANOS": [
        "MÃO DE OBRA", "MAO DE OBRA", "DIÁRIA", "DIARIA", "SALÁRIO", "SALARIO",
        "ENCARGO", "FOLHA DE PAGAMENTO", "FGTS", "INSS", "HONORÁRIO TRABALHISTA",
        "SERVIÇO TEMPORÁRIO"
    ],
    "SERVIÇOS OPERACIONAIS": [
        "FRETE", "TRANSPORTE", "COLHEITA", "SECAGEM", "ARMAZENAGEM",
        "PULVERIZAÇÃO", "PULVERIZACAO", "APLICAÇÃO AÉREA", "TRANSBORDO",
        "SILAGEM"
    ],
    "INFRAESTRUTURA E UTILIDADES": [
        "ENERGIA ELÉTRICA", "ENERGIA ELETRICA", "LUZ", "ÁGUA", "AGUA",
        "ARRENDAMENTO", "CONSTRUÇÃO", "CONSTRUCAO", "REFORMA", "MATERIAL HIDRÁULICO",
        "HIDRAULICO", "CIMENTO", "TIJOLO", "AREIA", "BRITA", "MADEIRA",
        "CERCA", "ARAME", "TUBO", "CANO PVC"
    ],
    "ADMINISTRATIVAS": [
        "HONORÁRIOS CONTÁBEIS", "HONORARIOS", "CONTABILIDADE", "ADVOCACIA",
        "AGRONÔMICO", "CONSULTORIA", "DESPESA BANCÁRIA", "TARIFA BANCÁRIA",
        "TAXA BANCÁRIA", "INTERNET", "TELEFONE", "SOFTWARE", "LICENÇA"
    ],
    "SEGUROS E PROTEÇÃO": [
        "SEGURO AGRÍCOLA", "SEGURO AGRICOLA", "APÓLICE", "APOLICE", "SINISTRO",
        "SEGURO DE MÁQUINA", "SEGURO PRESTAMISTA", "SEGURO PATRIMONIAL"
    ],
    "IMPOSTOS E TAXAS": [
        "ITR", "IPTU", "IPVA", "INCRA", "CCIR", "TAXA DE FISCALIZAÇÃO", "DARF",
        "GUIA DE RECOLHIMENTO"
    ],
    "INVESTIMENTOS": [
        "AQUISIÇÃO DE MÁQUINAS", "TRATOR", "COLHEITADEIRA", "PLANTADEIRA",
        "PULVERIZADOR AUTOPROPELIDO", "VEÍCULO", "CAMINHONETE", "CAMINHÃO",
        "IMÓVEL", "TERRA", "INFRAESTRUTURA RURAL", "SILO", "BARRACÃO", "PIVÔ CENTRAL"
    ]
}


class Agente:
    def __init__(self, api_key=None):
        load_dotenv(override=True)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()

    def _extrair_texto_pdf(self, pdf_file):
        """Extrai todo o texto legível das páginas do arquivo PDF preservando o layout visual de tabelas."""
        try:
            if isinstance(pdf_file, (str, os.PathLike)):
                reader = PdfReader(pdf_file)
            elif hasattr(pdf_file, "read"):
                # Arquivo em stream ou FileStorage do Flask
                pdf_file.seek(0)
                reader = PdfReader(pdf_file)
            elif isinstance(pdf_file, (bytes, bytearray)):
                reader = PdfReader(io.BytesIO(pdf_file))
            else:
                raise ValueError("Tipo de arquivo PDF não suportado.")

            text_parts = []
            for i, page in enumerate(reader.pages):
                try:
                    t = page.extract_text(extraction_mode="layout")
                except Exception:
                    t = page.extract_text()
                
                if t:
                    text_parts.append(f"--- PÁGINA {i+1} ---\n{t}")
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Aviso ao extrair texto do PDF: {e}")
            return ""

    def _classificar_por_regras(self, texto_completo, descricao_produtos=""):
        """Classifica os produtos da NF detectando termos e aplicando as regras definidas."""
        conteudo_busca = f"{descricao_produtos} {texto_completo}".upper()
        
        melhor_categoria = "classificação"
        melhores_termos = []
        maior_pontuacao = 0

        for categoria, termos in CATEGORIAS_SINAIS.items():
            encontrados = []
            for termo in termos:
                if re.search(r'\b' + re.escape(termo) + r'\b', conteudo_busca) or termo in conteudo_busca:
                    if termo not in encontrados:
                        encontrados.append(termo)
            if len(encontrados) > maior_pontuacao:
                maior_pontuacao = len(encontrados)
                melhor_categoria = categoria
                melhores_termos = encontrados

        if maior_pontuacao == 0:
            melhor_categoria = "classificação"
            melhores_termos = []

        return melhor_categoria, melhores_termos

    def _extrair_nome_emitente(self, texto_pdf):
        """Extrai o nome do emitente da nota com alta precisão."""
        # 1. Tenta extrair do canhoto: RECEBI(EMOS) DE [EMITENTE], OS PRODUTOS...
        m1 = re.search(r'RECEB[EI](?:\(EMOS\)|MOS)?\s+DE\s+([^,]+?)(?:,|\s+OS\s+PRODUTOS)', texto_pdf, re.IGNORECASE)
        if m1 and len(m1.group(1).strip()) > 3:
            nome = m1.group(1).strip()
            # Remove ruídos de início de linha
            nome = re.sub(r'^[^\w]+', '', nome)
            return nome

        # 2. Tenta extrair do quadro do emitente antes do endereço (Rua, Av, etc)
        m2 = re.search(r'(?:^|\n)\s*([A-Z0-9\s\.\-&/]+?(?:LTDA|S\.A\.|S/A|EIRELI|ME|EPP))\s*\n\s*(?:R\s+|RUA|AV|RODOVIA|ROD|PRAÇA|ALAMEDA|ESTRADA|SETOR|AVENIDA)', texto_pdf, re.IGNORECASE)
        if m2 and len(m2.group(1).strip()) > 3:
            return m2.group(1).strip()

        # 3. Padrão flexível na seção anterior a DESTINATÁRIO
        idx_dest = texto_pdf.find('DESTINATÁRIO/REMETENTE')
        texto_emitente = texto_pdf[:idx_dest] if idx_dest != -1 else texto_pdf
        linhas = [l.strip() for l in texto_emitente.split('\n') if l.strip()]
        for l in linhas:
            if re.search(r'\b(LTDA|S\.A\.|S/A|EIRELI)\b', l, re.IGNORECASE):
                if not re.search(r'RECEB|ATESTAMOS|SEFAZ|DANFE|CHAVE|PORTAL', l, re.IGNORECASE):
                    return l

        return None

    def _extrair_data_emissao(self, texto_pdf):
        """Extrai a data de emissão especificada na NF."""
        # 1. Campo explícito DATA DA EMISSÃO
        m = re.search(r'DATA\s+(?:DA\s+|DE\s+)?EMISS[ÃA]O[\s\S]*?(\d{2}[/\.]\d{2}[/\.]\d{4})', texto_pdf, re.IGNORECASE)
        if m:
            return m.group(1).replace('.', '/')
        
        # 2. Fallback para primeira data válida
        datas = re.findall(r'\b(\d{2}[/\.]\d{2}[/\.]\d{4})\b', texto_pdf)
        if datas:
            return datas[0].replace('.', '/')
        return None

    def _extrair_data_vencimento(self, texto_pdf, data_emissao=None):
        """
        Extrai a data de vencimento real localizada em FATURA/DUPLICATAS ou vencimento.
        """
        # 1. Seção FATURA / DUPLICATAS
        fatura_block = re.search(r'(?:FATURA|DUPLICATA)[\s\S]*?(?=CÁLCULO DO IMPOSTO|DADOS DOS PRODUTOS|TRANSPORTADOR|VALOR TOTAL|$)', texto_pdf, re.IGNORECASE)
        if fatura_block:
            texto_fatura = fatura_block.group(0)
            datas_fatura = re.findall(r'\b(\d{2}[/\.]\d{2}[/\.]\d{4})\b', texto_fatura)
            if datas_fatura:
                return datas_fatura[0].replace('.', '/')

        # 2. Menção explícita de VENCIMENTO ou PAGAMENTO
        venc_match = re.search(r'(?:VENCIMENTO|VENC\.?|DT\.?\s*VENC\.?|PAGAMENTO)[:\s]*(\d{2}[/\.]\d{2}[/\.]\d{4})', texto_pdf, re.IGNORECASE)
        if venc_match:
            return venc_match.group(1).replace('.', '/')

        # 3. Fallback: data de emissão
        return data_emissao

    def _extrair_fallback_heuristico(self, texto_pdf):
        """
        Parser heurístico robusto para extrair os campos principais caso a chave
        do Gemini não esteja configurada ou a chamada à LLM falhe temporariamente.
        """
        # Número da Nota Fiscal (ex: No. 000126981 ou Nº 000.084.682)
        nf_match = re.search(r'(?:Nº|Nº\.|No\.|Nº\s*|No\s*|NF-e\s*N[ºo°\.]\s*)(\d{3}(?:\.\d{3})+|\d{6,9})', texto_pdf, re.IGNORECASE)
        if not nf_match:
            nf_match = re.search(r'N[ºo°\.\s]*[:\.\s]*(\d{6,9}|\d{3}\.\d{3}\.\d{3})', texto_pdf, re.IGNORECASE)
        numero_nf = nf_match.group(1) if nf_match else None

        # Datas
        data_emissao = self._extrair_data_emissao(texto_pdf)
        data_vencimento = self._extrair_data_vencimento(texto_pdf, data_emissao)

        # Bloco Destinatário
        dest_block = re.search(r'DESTINATÁRIO/REMETENTE[\s\S]*?(?=INFORMAÇÕES|CÁLCULO DO IMPOSTO|DADOS DOS PRODUTOS|$)', texto_pdf, re.IGNORECASE)
        texto_destinatario = dest_block.group(0) if dest_block else ""

        # Bloco Emitente
        idx_dest = texto_pdf.find('DESTINATÁRIO/REMETENTE')
        texto_emitente = texto_pdf[:idx_dest] if idx_dest != -1 else texto_pdf

        # CNPJs / CPFs
        cnpjs_emit = re.findall(r'\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b', texto_emitente)
        cnpjs_dest = re.findall(r'\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b', texto_destinatario)
        cpfs_dest = re.findall(r'\b(\d{3}\.\d{3}\.\d{3}-\d{2})\b', texto_destinatario)

        cnpj_emitente = cnpjs_emit[0] if cnpjs_emit else None
        cnpj_destinatario = cnpjs_dest[0] if cnpjs_dest else (cpfs_dest[0] if cpfs_dest else None)

        # Nome do Emitente
        nome_emitente = self._extrair_nome_emitente(texto_pdf)

        # Nome do Destinatário
        nome_destinatario = None
        if texto_destinatario:
            lines = [l.strip() for l in texto_destinatario.split('\n') if l.strip()]
            for i, l in enumerate(lines):
                if 'NOME/RAZÃO SOCIAL' in l.upper() or 'NOME / RAZÃO SOCIAL' in l.upper():
                    if i + 1 < len(lines):
                        nome_destinatario = re.split(r'\s{2,}|\b\d{2}\.\d{3}', lines[i+1])[0].strip()
                        break

        # Valor Total da NF (V.TOT. DA NF ou VALOR TOTAL DA NOTA)
        valor_total = None
        vtot_block = re.search(r'VALOR TOTAL DA NOTA[^\n]*\n([^\n]+)', texto_pdf)
        if not vtot_block:
            vtot_block = re.search(r'V\.TOT\. DA NF[^\n]*\n([^\n]+)', texto_pdf)
        
        if vtot_block:
            linha_valores = vtot_block.group(1)
            valores_encontrados = re.findall(r'\b(\d{1,3}(?:\.\d{3})*,\d{2})\b', linha_valores)
            if valores_encontrados:
                valor_total = valores_encontrados[-1]

        if not valor_total:
            valores_gerais = re.findall(r'\b(\d{1,3}(?:\.\d{3})*,\d{2})\b', texto_pdf)
            valor_total = valores_gerais[-1] if valores_gerais else None

        # Extração heurística de produtos linha a linha
        produtos = []
        linhas_pdf = texto_pdf.split("\n")
        em_produtos = False
        for linha in linhas_pdf:
            if "DADOS DOS PRODUTOS" in linha.upper() or ("CÓDIGO" in linha.upper() and "DESCRIÇÃO" in linha.upper()):
                em_produtos = True
                continue
            if em_produtos and ("DADOS ADICIONAIS" in linha.upper() or "CÁLCULO DO ISSQN" in linha.upper() or "INFORMAÇÕES COMPLEMENTARES" in linha.upper()):
                em_produtos = False
                break
            if em_produtos and linha.strip():
                match_prod = re.search(r'([A-Z0-9/\-]+)\s+([A-Z0-9\s\./\-\(\)]+?)\s+(\d{8})\s+(\d{3})(\d{4})\s+([A-Z]{1,3})\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)', linha)
                if not match_prod:
                    match_prod = re.search(r'([A-Z0-9/\-]+)\s+([A-Z0-9\s\./\-\(\)]+?)\s+(\d{8})\s+(\d{3,4})\s+(\d{4})\s+([A-Z]{1,3})\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)', linha)
                
                if match_prod:
                    produtos.append({
                        "descricao": match_prod.group(2).strip()
                    })

        descricoes_lista = [p["descricao"] for p in produtos if p.get("descricao")]
        descricao_produtos = ", ".join(descricoes_lista) if descricoes_lista else "ITENS DA NOTA FISCAL"

        # Classificação
        categoria, termos = self._classificar_por_regras(texto_pdf, descricao_produtos)

        return {
            "Número da Nota Fiscal": numero_nf,
            "Data de Emissão": data_emissao,
            "Data de Vencimento": data_vencimento,
            "Descrição dos Produtos": descricao_produtos,
            "Valor Total": valor_total,
            "Nome do Emitente": nome_emitente,
            "CNPJ do Emitente": cnpj_emitente,
            "Nome do Destinatário": nome_destinatario,
            "CNPJ do Destinatário": cnpj_destinatario,
            "CLASSIFICAÇÃO": {
                "categoria": categoria,
                "termos_detectados": termos
            }
        }

    def extrair_dados(self, pdf_file, prompt=None):
        """
        Extrai informações de notas fiscais utilizando Gemini ou fallback heurístico.
        Retorna estritamente o JSON com as chaves padronizadas.
        """
        texto_pdf = self._extrair_texto_pdf(pdf_file)

        if not prompt:
            prompt = """
        Você é um especialista em análise de Notas Fiscais Eletrônicas (DANFE) e documentos fiscais.
        Sua tarefa é analisar rigorosamente o texto do documento fornecido e extrair os dados em formato JSON.

        INSTRUÇÕES DE EXTRAÇÃO:
        1. "Número da Nota Fiscal": número sequencial da nota fiscal (ex: "000.084.682" ou "000084682").
        2. "Data de Emissão": data localizada no campo "DATA DA EMISSÃO" (no formato DD/MM/AAAA).
        3. "Data de Vencimento": data de vencimento da fatura/duplicata localizada em "FATURA/DUPLICATAS" ou "VENCIMENTO" (ex: "001: 17/10/2025" -> extraia "17/10/2025"). 
           IMPORTANTE: NÃO confunda com a Data de Saída nem com a Data de Emissão! Se houver "FATURA/DUPLICATAS", pegue a data de vencimento da parcela. Somente se não houver fatura/duplicata/vencimento algum, use a data de emissão.
        4. "Nome do Emitente": Razão social da empresa emissora/vendedora localizada no cabeçalho ou no canhoto "RECEBI(EMOS) DE [EMITENTE]" (ex: "IGUACU MAQUINAS AGRICOLAS LTDA"). NÃO confunda com o destinatário e não retorne null!
        5. "CNPJ do Emitente": CNPJ da empresa emitente no formato XX.XXX.XXX/XXXX-XX.
        6. "Nome do Destinatário": Razão social ou nome completo localizado estritamente dentro da seção "DESTINATÁRIO/REMETENTE" (ex: "CICLANO DA SILVA").
        7. "CNPJ do Destinatário": CNPJ ou CPF do comprador localizado na seção "DESTINATÁRIO/REMETENTE".
        8. "Valor Total": valor total final da nota fiscal localizado em "VALOR TOTAL DA NOTA" ou "V.TOT. DA NF" (ex: "3.086,75").
        9. "Descrição dos Produtos": uma string concatenada com os nomes/descrições de TODOS os produtos/serviços, separados por vírgula.

        REGRAS DE CLASSIFICAÇÃO:
        Classifique a Nota Fiscal em uma das categorias abaixo com base nas descrições dos produtos e serviços:
        - MANUTENÇÃO E OPERAÇÃO: Combustíveis e Lubrificantes (Diesel, Graxa, Óleo), Peças, Parafusos, Anel, Bucha, Rolamento, Componentes Mecânicos, Manutenção de máquinas, Pneus, Filtros, Correias, Estopa, Pano de limpeza, Limpador.
        - INSUMOS AGRÍCOLAS: Sementes, Fertilizantes, Adubos, Defensivos Agrícolas, Corretivos, Calcário, Herbicida, Fungicida, Inseticida.
        - RECURSOS HUMANOS: Mão de Obra Temporária, Salários e Encargos, Diárias.
        - SERVIÇOS OPERACIONAIS: Frete e Transporte, Colheita Terceirizada, Secagem e Armazenagem, Pulverização e aplicação aérea.
        - INFRAESTRUTURA E UTILIDADES: Energia Elétrica, Água, Arrendamento, Material de Construção, Cimento, Madeira, Arame.
        - ADMINISTRATIVAS: Honorários Contábeis, Advocacia, Consultoria, Tarifas Bancárias, Internet, Software.
        - SEGUROS E PROTEÇÃO: Seguro Agrícola, Apólice, Seguro de Máquinas.
        - IMPOSTOS E TAXAS: ITR, IPTU, IPVA, INCRA, DARF.
        - INVESTIMENTOS: Aquisição de Máquinas e Implementos, Trator, Colheitadeira, Veículos, Imóveis.

        Retorne também um objeto "CLASSIFICAÇÃO" com as chaves:
        - "categoria": string com o nome exato da categoria identificada.
        - "termos_detectados": lista de strings com os termos encontrados no texto que motivaram a classificação.

        Retorne estritamente o JSON válido correspondente, sem textos explicativos antes ou depois.
        """

        # Exige a chave da API Gemini (sem fallback silencioso)
        if not self.api_key:
            raise ValueError("Chave da API Gemini não informada! Por favor, informe sua chave no campo da interface ou configure GEMINI_API_KEY no arquivo .env.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        
        conteudo_prompt = f"{prompt}\n\n--- TEXTO EXTRAÍDO DA NOTA FISCAL (TODAS AS PÁGINAS) ---\n{texto_pdf}"
        
        # Lista de modelos oficiais e disponíveis na Google Gemini API
        modelos_tentativa = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
        ]
        response = None
        ultimo_erro = None
        modelo_utilizado = None

        for mod in modelos_tentativa:
            try:
                response = client.models.generate_content(
                    model=mod,
                    contents=conteudo_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    modelo_utilizado = mod
                    break
            except Exception as err_mod:
                ultimo_erro = err_mod
                continue

        if not response or not response.text:
            raise Exception(f"Erro ao chamar a API Gemini: {ultimo_erro}")

        resposta_texto = response.text.strip()
        if resposta_texto.startswith("```"):
            resposta_texto = re.sub(r"^```[a-zA-Z]*\n?", "", resposta_texto)
            resposta_texto = re.sub(r"\n?```$", "", resposta_texto).strip()

        dados = json.loads(resposta_texto)
        resultado = self._normalizar_json(dados, texto_pdf)
        resultado["_origem"] = f"Google Gemini IA ({modelo_utilizado})"
        return resultado

    def _normalizar_json(self, dados, texto_pdf=""):
        """
        Garante conformidade estrita com a estrutura esperada no projeto,
        removendo a chave 'produtos' e normalizando os campos principais.
        """
        def get_val(chaves, default=None):
            for k in chaves:
                if k in dados and dados[k] is not None:
                    v = str(dados[k]).strip()
                    if v and v.lower() != "null":
                        return v
            return default

        num_nf = get_val(["Número da Nota Fiscal", "numero_nota_fiscal", "numero_nf", "numero da nota fiscal", "numero"])
        dt_emissao = get_val(["Data de Emissão", "data_emissao", "data de emissao", "emissao"])
        dt_venc = get_val(["Data de Vencimento", "data_vencimento", "data de vencimento", "vencimento"])
        val_total = get_val(["Valor Total", "valor_total", "valor total", "valor"])
        nome_emit = get_val(["Nome do Emitente", "nome_emitente", "nome do emitente", "emitente", "razao_social_emitente"])
        cnpj_emit = get_val(["CNPJ do Emitente", "cnpj_emitente", "cnpj do emitente"])
        nome_dest = get_val(["Nome do Destinatário", "nome_destinatario", "nome do destinatario", "destinatario"])
        cnpj_dest = get_val(["CNPJ do Destinatário", "cnpj_destinatario", "cnpj do destinatario", "cpf_destinatario", "CPF do Destinatário"])

        # Proteções caso a IA retorne nulo ou data errada
        if not nome_emit and texto_pdf:
            nome_emit = self._extrair_nome_emitente(texto_pdf)

        if not dt_emissao and texto_pdf:
            dt_emissao = self._extrair_data_emissao(texto_pdf)

        if (not dt_venc or dt_venc == dt_emissao) and texto_pdf:
            dt_venc_recuperada = self._extrair_data_vencimento(texto_pdf, dt_emissao)
            if dt_venc_recuperada:
                dt_venc = dt_venc_recuperada

        # Tratar a 'Descrição dos Produtos' caso a LLM tenha retornado os produtos em forma de lista ou texto
        desc_prod_val = dados.get("Descrição dos Produtos") or dados.get("descricao_produtos")
        if not desc_prod_val:
            prods_list = dados.get("produtos") or dados.get("itens")
            if isinstance(prods_list, list):
                nomes = [p.get("descricao") or p.get("description") or str(p) for p in prods_list if isinstance(p, dict)]
                desc_prod = ", ".join(filter(None, nomes))
            else:
                desc_prod = str(prods_list) if prods_list else ""
        else:
            desc_prod = str(desc_prod_val).strip()

        # Classificação
        classificacao_obj = dados.get("CLASSIFICAÇÃO") or dados.get("classificacao") or dados.get("classificação") or {}
        if isinstance(classificacao_obj, dict):
            categoria = classificacao_obj.get("categoria", "classificação")
            termos = classificacao_obj.get("termos_detectados", [])
        else:
            categoria = str(classificacao_obj)
            termos = []

        if not categoria or categoria.lower() == "desconhecida":
            categoria, termos_fallback = self._classificar_por_regras(texto_pdf, desc_prod)
            if not termos:
                termos = termos_fallback

        return {
            "Número da Nota Fiscal": num_nf,
            "Data de Emissão": dt_emissao,
            "Data de Vencimento": dt_venc,
            "Descrição dos Produtos": desc_prod,
            "Valor Total": val_total,
            "Nome do Emitente": nome_emit,
            "CNPJ do Emitente": cnpj_emit,
            "Nome do Destinatário": nome_dest,
            "CNPJ do Destinatário": cnpj_dest,
            "CLASSIFICAÇÃO": {
                "categoria": categoria,
                "termos_detectados": termos if isinstance(termos, list) else ([termos] if termos else [])
            }
        }
