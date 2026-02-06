"""
PDF 导入功能测试工具
===================
用于诊断 PDF 导入功能是否正常工作。
运行：python test_pdf_import.py
"""

from __future__ import annotations

import sys


def test_pymupdf_import():
    """测试 PyMuPDF 是否能正常导入"""
    print("=" * 60)
    print("测试 1: PyMuPDF 导入")
    print("=" * 60)
    
    try:
        import fitz  # PyMuPDF
        print("✅ PyMuPDF 导入成功")
        
        # 显示版本信息
        try:
            version = fitz.version
            print(f"   版本：{version}")
        except:
            print("   （无法获取版本信息）")
        
        return True
    except ImportError as e:
        print(f"❌ PyMuPDF 导入失败：{str(e)}")
        print("\n解决方案：")
        print("  pip install pymupdf")
        return False
    except Exception as e:
        print(f"❌ PyMuPDF 导入异常：{str(e)}")
        return False


def test_pdf_extraction():
    """测试 PDF 文本提取功能"""
    print("\n" + "=" * 60)
    print("测试 2: PDF 文本提取功能")
    print("=" * 60)
    
    try:
        from pdf_resume_import import extract_pdf_text
        print("✅ PDF 提取模块导入成功")
        
        # 检查是否有测试 PDF 文件
        import os
        test_pdf_paths = [
            "test_data/简历_张伟_博士.pdf",
            "test_data/简历_陈静_硕士.pdf",
        ]
        
        found_pdf = None
        for pdf_path in test_pdf_paths:
            if os.path.exists(pdf_path):
                found_pdf = pdf_path
                break
        
        if found_pdf:
            print(f"\n找到测试 PDF：{found_pdf}")
            try:
                with open(found_pdf, "rb") as f:
                    pdf_bytes = f.read()
                
                print("正在提取文本...")
                result = extract_pdf_text(pdf_bytes, ocr_enabled=False)
                
                print(f"✅ PDF 提取成功")
                print(f"   提取方式：{result.method}")
                print(f"   页数：{result.page_count}")
                print(f"   文本长度：{len(result.text)} 字符")
                
                if result.text:
                    preview = result.text[:200].replace("\n", " ")
                    print(f"   文本预览：{preview}...")
                else:
                    print("   ⚠️ 提取的文本为空")
                
                return True
            except Exception as e:
                print(f"❌ PDF 提取失败：{str(e)}")
                import traceback
                print("\n详细错误：")
                print(traceback.format_exc())
                return False
        else:
            print("⚠️ 未找到测试 PDF 文件")
            print("   请上传一个 PDF 文件进行测试")
            return None
        
    except ImportError as e:
        print(f"❌ PDF 提取模块导入失败：{str(e)}")
        return False
    except Exception as e:
        print(f"❌ 测试异常：{str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_easyocr_import():
    """测试 EasyOCR 是否能正常导入（OCR 功能）"""
    print("\n" + "=" * 60)
    print("测试 3: EasyOCR 导入（OCR 功能）")
    print("=" * 60)
    
    try:
        import easyocr
        print("✅ EasyOCR 导入成功")
        return True
    except ImportError:
        print("⚠️ EasyOCR 未安装（OCR 功能不可用）")
        print("   如需使用 OCR，请安装：pip install easyocr pillow numpy")
        return None
    except Exception as e:
        print(f"❌ EasyOCR 导入异常：{str(e)}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("PDF 导入功能诊断工具")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试 1: PyMuPDF
    results.append(("PyMuPDF", test_pymupdf_import()))
    
    # 测试 2: PDF 提取
    if results[0][1]:  # 只有 PyMuPDF 可用时才测试提取
        results.append(("PDF 提取", test_pdf_extraction()))
    else:
        results.append(("PDF 提取", False))
    
    # 测试 3: EasyOCR（可选）
    results.append(("EasyOCR", test_easyocr_import()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 跳过（可选）"
        print(f"{name:20s} {status}")
    
    # 给出建议
    print("\n" + "=" * 60)
    print("建议")
    print("=" * 60)
    
    if not results[0][1]:  # PyMuPDF 失败
        print("❌ 核心依赖缺失，PDF 导入功能不可用")
        print("\n请运行：")
        print("  pip install pymupdf")
        print("\n或安装所有依赖：")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    elif results[1][1] is False:  # PDF 提取失败
        print("⚠️ PDF 提取功能异常")
        print("请检查：")
        print("1. PDF 文件是否损坏")
        print("2. 是否有足够的权限读取文件")
        print("3. 查看上方的详细错误信息")
    else:
        print("✅ PDF 导入功能正常")
        if results[2][1] is None:
            print("\n提示：如需使用 OCR 功能（扫描件 PDF），请安装：")
            print("  pip install easyocr pillow numpy")


if __name__ == "__main__":
    main()
