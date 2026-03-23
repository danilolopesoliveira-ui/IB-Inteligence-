"""
Guarantee Analysis Tool
Analyzes different guarantee types for credit operations:
- Real estate (imóveis): LTV from matrícula/appraisal
- Receivables (recebíveis/duplicatas): coverage, concentration, aging
- Agricultural production (produção agrícola): crop value estimation
- Equipment/infrastructure: book value and depreciation
- Personal/cross guarantees: qualitative assessment

Accepts Excel (.xlsx/.csv) or PDF files as input.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class GuaranteeInput(BaseModel):
    guarantee_type: str = Field(
        description=(
            "Tipo de garantia: 'imovel' | 'recebiveis' | 'producao_agricola' | "
            "'equipamentos' | 'aval_pessoal' | 'aval_cruzado'"
        )
    )
    file_path: str = Field(
        default="",
        description=(
            "Caminho absoluto para o arquivo de garantia. "
            "PDF para matrículas/laudos, Excel/CSV para recebíveis/planilhas."
        ),
    )
    manual_data: str = Field(
        default="{}",
        description=(
            "JSON com dados manuais quando não há arquivo. Campos variam por tipo. "
            "Exemplos: "
            "imovel: {'valor_avaliacao': 5000000, 'area_m2': 2000, 'municipio': 'Goiania', 'matricula': '12345'} "
            "recebiveis: {'volume_total': 2000000, 'prazo_medio_dias': 45, 'concentracao_top3_pct': 35, 'inadimplencia_pct': 2.5} "
            "producao_agricola: {'area_hectares': 500, 'cultura': 'soja', 'produtividade_scs_ha': 58, 'preco_saca': 125} "
            "equipamentos: {'valor_contabil': 800000, 'ano_fabricacao': 2020, 'vida_util_anos': 10}"
        ),
    )
    operation_volume: float = Field(
        default=0.0,
        description="Volume total da operação em BRL, para calcular cobertura/LTV.",
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class GuaranteeAnalysisTool(BaseTool):
    name: str = "guarantee_analysis"
    description: str = (
        "Analisa garantias de operações de crédito: imóveis (LTV, matrícula), "
        "recebíveis (cobertura, aging, concentração), produção agrícola (valor de safra), "
        "equipamentos (valor depreciado), aval pessoal/cruzado. "
        "Aceita arquivos PDF (matrículas, laudos) ou Excel/CSV (carteiras de recebíveis). "
        "Retorna: valor da garantia, ratio de cobertura, qualidade e observações de crédito."
    )
    args_schema: type[BaseModel] = GuaranteeInput

    def _run(
        self,
        guarantee_type: str,
        file_path: str = "",
        manual_data: str = "{}",
        operation_volume: float = 0.0,
    ) -> str:
        try:
            data = json.loads(manual_data)
            file_content = self._read_file(file_path) if file_path else {}

            # Merge file content with manual data (manual overrides)
            merged = {**file_content, **data}

            handler = {
                "imovel":           self._analyze_imovel,
                "recebiveis":       self._analyze_recebiveis,
                "producao_agricola": self._analyze_producao_agricola,
                "equipamentos":     self._analyze_equipamentos,
                "aval_pessoal":     self._analyze_aval_pessoal,
                "aval_cruzado":     self._analyze_aval_cruzado,
            }.get(guarantee_type.lower())

            if not handler:
                return json.dumps({"error": f"Tipo de garantia desconhecido: {guarantee_type}"})

            result = handler(merged)
            result["guarantee_type"] = guarantee_type
            result["file_analyzed"] = os.path.basename(file_path) if file_path else None

            if operation_volume > 0 and result.get("guarantee_value"):
                coverage = result["guarantee_value"] / operation_volume
                result["coverage_ratio"] = round(coverage, 3)
                result["coverage_label"] = (
                    "EXCELENTE (>2.0x)" if coverage >= 2.0 else
                    "ADEQUADO (1.3x–2.0x)" if coverage >= 1.3 else
                    "MINIMO (1.0x–1.3x)" if coverage >= 1.0 else
                    "INSUFICIENTE (<1.0x)"
                )

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro na análise de garantia: {exc}")
            return json.dumps({"error": str(exc)})

    # ------------------------------------------------------------------
    # File reader (dispatches by extension)
    # ------------------------------------------------------------------

    def _read_file(self, path: str) -> dict:
        """Extract structured data from PDF or Excel/CSV guarantee files."""
        ext = Path(path).suffix.lower()
        result = {}

        if ext == ".pdf":
            result = self._read_pdf(path)
        elif ext in (".xlsx", ".xls"):
            result = self._read_excel(path)
        elif ext == ".csv":
            result = self._read_csv(path)

        return result

    def _read_pdf(self, path: str) -> dict:
        """Extract text from PDF (matricula, laudo de avaliacao)."""
        try:
            import pdfplumber
            text_blocks = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_blocks.append(t)
            full_text = "\n".join(text_blocks)
            # Return raw text for LLM to parse
            return {"pdf_text": full_text[:8000], "pages": len(text_blocks)}
        except ImportError:
            logger.warning("pdfplumber not installed — install with: pip install pdfplumber")
            return {"pdf_error": "pdfplumber not installed"}
        except Exception as e:
            return {"pdf_error": str(e)}

    def _read_excel(self, path: str) -> dict:
        """Parse Excel receivables portfolio or appraisal."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            ws = wb.active
            rows = []
            headers = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(c) if c else f"col_{i}" for i, c in enumerate(row)]
                elif i < 200:  # read up to 200 rows
                    rows.append(dict(zip(headers, row)))
            wb.close()

            # Basic stats
            numeric_cols = {}
            for row in rows:
                for k, v in row.items():
                    if isinstance(v, (int, float)):
                        numeric_cols.setdefault(k, []).append(v)

            stats = {col: {"sum": sum(vals), "avg": sum(vals)/len(vals), "count": len(vals)}
                     for col, vals in numeric_cols.items()}

            return {"excel_headers": headers, "row_count": len(rows), "numeric_summary": stats}
        except ImportError:
            return {"excel_error": "openpyxl not installed"}
        except Exception as e:
            return {"excel_error": str(e)}

    def _read_csv(self, path: str) -> dict:
        """Parse CSV receivables file."""
        try:
            import csv
            rows = []
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= 200:
                        break
                    rows.append(row)
            return {"csv_row_count": len(rows), "csv_headers": list(rows[0].keys()) if rows else []}
        except Exception as e:
            return {"csv_error": str(e)}

    # ------------------------------------------------------------------
    # Guarantee type analyzers
    # ------------------------------------------------------------------

    def _analyze_imovel(self, data: dict) -> dict:
        valor = float(data.get("valor_avaliacao", 0))
        area = float(data.get("area_m2", 0) or data.get("area_hectares", 0))
        municipio = data.get("municipio", "")
        matricula = data.get("matricula", "")
        onus = data.get("onus_reais", "Não informado")
        pdf_text = data.get("pdf_text", "")

        quality_flags = []
        quality_score = 100

        if not matricula:
            quality_flags.append("Número de matrícula não informado — verificar junto ao cartório")
            quality_score -= 15
        if onus and onus not in ["Nenhum", "Não informado", ""]:
            quality_flags.append(f"Ônus reais identificados: {onus} — avaliar impacto na liquidez")
            quality_score -= 20
        if not municipio:
            quality_flags.append("Município não identificado — verificar liquidez regional")
            quality_score -= 10

        # PDF hint
        if pdf_text:
            if "penhora" in pdf_text.lower() or "hipoteca" in pdf_text.lower():
                quality_flags.append("ALERTA: Penhora ou hipoteca mencionada no PDF — revisão urgente")
                quality_score -= 30
            if "alienação fiduciária" in pdf_text.lower():
                quality_flags.append("Alienação fiduciária já constituída — verificar saldo devedor")
                quality_score -= 15

        discount_pct = 0.30  # standard 30% haircut on real estate for credit
        discounted_value = valor * (1 - discount_pct)

        return {
            "guarantee_value": round(discounted_value, 0),
            "gross_value": round(valor, 0),
            "discount_applied_pct": f"{discount_pct*100:.0f}% (haircut padrão imóvel)",
            "area": f"{area:,.0f} m² / ha" if area else "Não informado",
            "municipio": municipio or "Não informado",
            "matricula": matricula or "Não informado",
            "onus_reais": onus,
            "quality_score": max(quality_score, 0),
            "quality_label": (
                "EXCELENTE" if quality_score >= 85 else
                "BOM" if quality_score >= 70 else
                "REGULAR" if quality_score >= 50 else
                "FRACO"
            ),
            "observations": quality_flags or ["Garantia real em ordem. Prosseguir com avaliação independente."],
            "next_steps": [
                "Obter laudo de avaliação de perito independente",
                "Verificar certidão de ônus reais atualizada no cartório",
                "Confirmar IPTU em dia e certidão negativa de débitos municipais",
                "Constituir alienação fiduciária ou hipoteca sobre o imóvel",
            ],
        }

    def _analyze_recebiveis(self, data: dict) -> dict:
        volume = float(data.get("volume_total", 0))
        prazo_medio = float(data.get("prazo_medio_dias", 30))
        concentracao = float(data.get("concentracao_top3_pct", 0))  # % dos 3 maiores
        inadimplencia = float(data.get("inadimplencia_pct", 0))
        setor_devedor = data.get("setor_devedor", "")
        tipo = data.get("tipo_recebiveis", "duplicatas")

        quality_flags = []
        quality_score = 100

        # Standard advance rate: 75-85% for receivables
        advance_rate = 0.80
        if concentracao > 50:
            quality_flags.append(f"Concentração elevada: top 3 devedores = {concentracao:.1f}% — risco de contraparte")
            quality_score -= 20
            advance_rate = 0.70
        elif concentracao > 30:
            quality_flags.append(f"Concentração moderada: top 3 = {concentracao:.1f}%")
            quality_score -= 10

        if inadimplencia > 5:
            quality_flags.append(f"Inadimplência elevada: {inadimplencia:.1f}% — acima do benchmark de 3%")
            quality_score -= 25
            advance_rate -= 0.10
        elif inadimplencia > 2:
            quality_flags.append(f"Inadimplência em atenção: {inadimplencia:.1f}%")
            quality_score -= 10

        if prazo_medio > 90:
            quality_flags.append(f"Prazo médio longo: {prazo_medio:.0f} dias — verificar liquidez da carteira")
            quality_score -= 10

        eligible_value = volume * advance_rate

        return {
            "guarantee_value": round(eligible_value, 0),
            "portfolio_volume": round(volume, 0),
            "advance_rate_applied": f"{advance_rate*100:.0f}%",
            "prazo_medio_dias": prazo_medio,
            "concentracao_top3_pct": concentracao,
            "inadimplencia_pct": inadimplencia,
            "tipo_recebiveis": tipo,
            "quality_score": max(quality_score, 0),
            "quality_label": (
                "EXCELENTE" if quality_score >= 85 else
                "BOM" if quality_score >= 70 else
                "REGULAR" if quality_score >= 50 else
                "FRACO"
            ),
            "observations": quality_flags or ["Carteira de recebíveis em ordem para uso como garantia."],
            "next_steps": [
                "Formalizar cessão fiduciária dos recebíveis",
                "Realizar auditoria da carteira (aging e concentração)",
                "Estabelecer conta vinculada para liquidação",
                "Definir gatilho de substituição de recebíveis (trigger)",
            ],
        }

    def _analyze_producao_agricola(self, data: dict) -> dict:
        area = float(data.get("area_hectares", 0))
        cultura = data.get("cultura", "soja")
        produtividade = float(data.get("produtividade_scs_ha", 58))  # sacas/ha
        preco_saca = float(data.get("preco_saca", 0))  # BRL

        # Default prices (illustrative — should come from CEPEA/B3)
        precos_referencia = {"soja": 125, "milho": 65, "cafe": 1200, "algodao": 230, "cana": 180}
        if not preco_saca:
            preco_saca = precos_referencia.get(cultura.lower(), 100)

        producao_total_scs = area * produtividade
        valor_bruto = producao_total_scs * preco_saca

        # Standard: 70% of gross value (weather/price risk)
        advance_rate = 0.70
        valor_garantia = valor_bruto * advance_rate

        quality_flags = []
        quality_score = 90

        if area < 100:
            quality_flags.append("Área pequena (<100 ha) — verificar viabilidade de CPR")
            quality_score -= 10
        if not data.get("safra_ano"):
            quality_flags.append("Ano-safra não informado — especificar para constituição do CPR")
            quality_score -= 5

        return {
            "guarantee_value": round(valor_garantia, 0),
            "gross_production_value": round(valor_bruto, 0),
            "advance_rate_applied": f"{advance_rate*100:.0f}%",
            "area_hectares": area,
            "cultura": cultura,
            "produtividade_scs_ha": produtividade,
            "producao_estimada_scs": round(producao_total_scs, 0),
            "preco_referencia_saca": preco_saca,
            "quality_score": max(quality_score, 0),
            "quality_label": "BOM" if quality_score >= 70 else "REGULAR",
            "observations": quality_flags or ["Produção agrícola qualificável como garantia via CPR."],
            "instrument": "CPR — Cédula do Produtor Rural",
            "next_steps": [
                "Emitir CPR financeira com endosso ao credor",
                "Contratar seguro agrícola sobre a produção (PROAGRO ou privado)",
                "Verificar possibilidade de hedge de preço (B3 futuros)",
                "Confirmar que produção não está alienada em outra operação",
            ],
        }

    def _analyze_equipamentos(self, data: dict) -> dict:
        valor_contabil = float(data.get("valor_contabil", 0))
        ano_fab = int(data.get("ano_fabricacao", 2020))
        vida_util = int(data.get("vida_util_anos", 10))
        descricao = data.get("descricao", "Equipamentos industriais")

        from datetime import date
        idade = date.today().year - ano_fab
        depreciacao_acumulada = min(idade / vida_util, 0.90)
        valor_residual = valor_contabil * (1 - depreciacao_acumulada)

        # Standard haircut: 40% on residual value for forced sale
        advance_rate = 0.60
        valor_garantia = valor_residual * advance_rate

        return {
            "guarantee_value": round(valor_garantia, 0),
            "book_value": round(valor_contabil, 0),
            "residual_value_estimated": round(valor_residual, 0),
            "advance_rate_applied": f"{advance_rate*100:.0f}% (haircut venda forçada)",
            "idade_anos": idade,
            "depreciacao_acumulada_pct": f"{depreciacao_acumulada*100:.1f}%",
            "descricao": descricao,
            "quality_label": "BOM" if idade <= 3 else "REGULAR" if idade <= 7 else "FRACO",
            "quality_score": max(90 - idade * 5, 30),
            "observations": [
                f"Equipamento com {idade} anos de uso ({depreciacao_acumulada*100:.0f}% depreciado)",
                "Recomendado laudo de avaliação independente para registro como garantia",
                "Verificar alienação fiduciária ou penhor mercantil existente",
            ],
            "next_steps": [
                "Laudo de avaliação por engenheiro credenciado",
                "Constituição de penhor mercantil ou alienação fiduciária",
                "Verificar apólice de seguro do ativo",
            ],
        }

    def _analyze_aval_pessoal(self, data: dict) -> dict:
        patrimonio = float(data.get("patrimonio_liquido", 0))
        dividas = float(data.get("dividas_pessoais", 0))
        renda_mensal = float(data.get("renda_mensal", 0))
        nome = data.get("nome_avalista", "Não informado")

        patrimonio_liquido = patrimonio - dividas

        return {
            "guarantee_value": round(patrimonio_liquido * 0.50, 0),  # 50% of net worth
            "patrimonio_bruto": round(patrimonio, 0),
            "dividas_declaradas": round(dividas, 0),
            "patrimonio_liquido_estimado": round(patrimonio_liquido, 0),
            "avalista": nome,
            "quality_label": "COMPLEMENTAR" if patrimonio_liquido > 0 else "INSUFICIENTE",
            "observations": [
                "Aval pessoal é garantia pessoal — depende de certidões negativas e patrimônio comprovado",
                "Solicitar declaração patrimonial atualizada",
                "Verificar certidão de protestos, ações cíveis e falências",
            ],
            "next_steps": [
                "Declaração patrimonial assinada pelo avalista",
                "Certidões negativas de débito federal, estadual e municipal",
                "Certidão de distribuição de ações cíveis e falências",
                "Verificar regime de casamento (se casado, cônjuge deve co-assinar)",
            ],
        }

    def _analyze_aval_cruzado(self, data: dict) -> dict:
        empresas = data.get("empresas", [])
        faturamento_total = float(data.get("faturamento_total_grupo", 0))
        ebitda_total = float(data.get("ebitda_total_grupo", 0))

        return {
            "guarantee_value": round(ebitda_total * 3 if ebitda_total else faturamento_total * 0.2, 0),
            "empresas_avalistas": empresas,
            "faturamento_grupo": round(faturamento_total, 0),
            "ebitda_grupo": round(ebitda_total, 0),
            "quality_label": "COMPLEMENTAR",
            "observations": [
                "Aval cruzado reforça a garantia quando o grupo tem empresas sólidas",
                "Verificar ausência de restrições societárias para prestação de aval",
                "Confirmar que não há cláusula de vedação a avais nos contratos sociais",
            ],
            "next_steps": [
                "Contrato social de cada empresa avalista",
                "Balanço patrimonial das empresas do grupo",
                "Certidões negativas de todas as empresas avalistas",
                "Aprovação em reunião de sócios/diretoria para prestação do aval",
            ],
        }
