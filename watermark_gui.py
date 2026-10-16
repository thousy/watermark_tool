import os
import sys
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Font resolution
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "C:/Windows/Fonts/simhei.ttf"

FONT_REG = "C:/Windows/Fonts/msyh.ttc"
if not os.path.exists(FONT_REG):
    FONT_REG = FONT_BOLD

PRESETS = {
    "【安防协会资质申报专用】": (
        "仅供办理广东省安防协会能力评价资质使用",
        "他用无效 · 严禁用于工程招投标与质量签字 · 复印无效"
    ),
    "【中级职称/资格证申报】": (
        "仅供企业申报技术资质使用 · 他用无效",
        "严禁用于工程项目挂靠、标书应答与签字验收"
    ),
    "【身份证/个人证件防盗用】": (
        "仅供办理XXXX业务核验身份使用",
        "再次复印无效 · 他用无效 · 严禁用于贷款或信用卡申请"
    ),
    "【通用业务办理免责】": (
        "仅供本次业务审核专项使用",
        "非本人原件签字认可之一律无效 · 复印作废"
    )
}

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("证件防盗用水印生成器 (Antigravity)")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)
        
        self.current_img = None
        self.watermarked_img = None
        self.current_filepath = ""
        self.watermark_color_rgb = (210, 35, 35) # Default dark red
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top toolbar
        top_frame = ttk.Frame(self.root, padding=8)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        btn_open = ttk.Button(top_frame, text="📂 打开图片...", command=self.open_image)
        btn_open.pack(side=tk.LEFT, padx=5)
        
        btn_batch = ttk.Button(top_frame, text="📁 批量处理文件夹...", command=self.batch_process)
        btn_batch.pack(side=tk.LEFT, padx=5)
        
        btn_save = ttk.Button(top_frame, text="💾 导出保存图片...", command=self.save_image)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        self.lbl_file_info = ttk.Label(top_frame, text="请先点击【打开图片】导入证件照片/扫描件", foreground="#555")
        self.lbl_file_info.pack(side=tk.LEFT, padx=15)
        
        # Main split container
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        # Left settings control panel (width ~ 360)
        left_container = ttk.Frame(paned, padding=6, width=380)
        paned.add(left_container, weight=0)
        
        # Right preview canvas
        right_container = ttk.Frame(paned, padding=6)
        paned.add(right_container, weight=1)
        
        self.build_settings_panel(left_container)
        self.build_preview_panel(right_container)
        
    def build_settings_panel(self, parent):
        # Scrollable canvas for controls if needed
        # Preset selection
        lf_preset = ttk.LabelFrame(parent, text=" 快速预设模板 ", padding=8)
        lf_preset.pack(fill=tk.X, pady=4)
        
        self.combo_preset = ttk.Combobox(lf_preset, values=list(PRESETS.keys()), state="readonly")
        self.combo_preset.current(0)
        self.combo_preset.pack(fill=tk.X)
        self.combo_preset.bind("<<ComboboxSelected>>", self.on_preset_selected)
        
        # Text settings
        lf_text = ttk.LabelFrame(parent, text=" 水印文字内容 ", padding=8)
        lf_text.pack(fill=tk.X, pady=4)
        
        ttk.Label(lf_text, text="主水印文字（第一行）：").pack(anchor=tk.W)
        self.txt_main = ttk.Entry(lf_text)
        self.txt_main.insert(0, PRESETS["【安防协会资质申报专用】"][0])
        self.txt_main.pack(fill=tk.X, pady=(2, 6))
        self.txt_main.bind("<KeyRelease>", lambda e: self.update_preview())
        
        ttk.Label(lf_text, text="副水印声明（第二行）：").pack(anchor=tk.W)
        self.txt_sub = ttk.Entry(lf_text)
        self.txt_sub.insert(0, PRESETS["【安防协会资质申报专用】"][1])
        self.txt_sub.pack(fill=tk.X, pady=2)
        self.txt_sub.bind("<KeyRelease>", lambda e: self.update_preview())
        
        # Style settings
        lf_style = ttk.LabelFrame(parent, text=" 水印排版模式 ", padding=8)
        lf_style.pack(fill=tk.X, pady=4)
        
        self.var_mode = tk.StringVar(value="tile")
        r1 = ttk.Radiobutton(lf_style, text="45° 全屏密集平铺（防盗防抠图首选）", value="tile", variable=self.var_mode, command=self.update_preview)
        r1.pack(anchor=tk.W, pady=2)
        r2 = ttk.Radiobutton(lf_style, text="居中斜向粗幅横带（高警示度）", value="banner", variable=self.var_mode, command=self.update_preview)
        r2.pack(anchor=tk.W, pady=2)
        r3 = ttk.Radiobutton(lf_style, text="右下角防伪专用印章框", value="stamp", variable=self.var_mode, command=self.update_preview)
        r3.pack(anchor=tk.W, pady=2)
        
        # Appearance parameters
        lf_param = ttk.LabelFrame(parent, text=" 水印外观参数调节 ", padding=8)
        lf_param.pack(fill=tk.X, pady=4)
        
        # Opacity
        row1 = ttk.Frame(lf_param)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="不透明度：").pack(side=tk.LEFT)
        self.slider_opacity = ttk.Scale(row1, from_=10, to=90, value=38, command=lambda v: self.update_preview())
        self.slider_opacity.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.lbl_opacity = ttk.Label(row1, text="38%", width=4)
        self.lbl_opacity.pack(side=tk.RIGHT)
        
        # Density / Spacing (for tile)
        row2 = ttk.Frame(lf_param)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="平铺间距：").pack(side=tk.LEFT)
        self.slider_density = ttk.Scale(row2, from_=150, to=450, value=260, command=lambda v: self.update_preview())
        self.slider_density.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Font size scale
        row3 = ttk.Frame(lf_param)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="文字大小：").pack(side=tk.LEFT)
        self.slider_fontsize = ttk.Scale(row3, from_=0.6, to=1.6, value=1.0, command=lambda v: self.update_preview())
        self.slider_fontsize.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Angle
        row4 = ttk.Frame(lf_param)
        row4.pack(fill=tk.X, pady=2)
        ttk.Label(row4, text="旋转角度：").pack(side=tk.LEFT)
        self.slider_angle = ttk.Scale(row4, from_=-60, to=60, value=32, command=lambda v: self.update_preview())
        self.slider_angle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Color chooser
        row5 = ttk.Frame(lf_param)
        row5.pack(fill=tk.X, pady=4)
        ttk.Label(row5, text="水印颜色：").pack(side=tk.LEFT)
        self.btn_color = tk.Button(row5, text="  ", bg="#d22323", width=4, relief="groove", command=self.choose_color)
        self.btn_color.pack(side=tk.LEFT, padx=6)
        
        btn_c_red = ttk.Button(row5, text="防伪红", width=6, command=lambda: self.set_color((210, 35, 35), "#d22323"))
        btn_c_red.pack(side=tk.LEFT, padx=2)
        btn_c_gray = ttk.Button(row5, text="中性灰", width=6, command=lambda: self.set_color((120, 120, 120), "#787878"))
        btn_c_gray.pack(side=tk.LEFT, padx=2)
        btn_c_blue = ttk.Button(row5, text="警示蓝", width=6, command=lambda: self.set_color((30, 80, 180), "#1e50b4"))
        btn_c_blue.pack(side=tk.LEFT, padx=2)
        
        # Actions
        btn_refresh = ttk.Button(parent, text="🔄 立即刷新效果", command=self.update_preview)
        btn_refresh.pack(fill=tk.X, pady=(10, 4))
        
    def build_preview_panel(self, parent):
        lf_preview = ttk.LabelFrame(parent, text=" 实时预览（自动保持原图比例） ", padding=6)
        lf_preview.pack(fill=tk.BOTH, expand=True)
        
        self.canvas_preview = tk.Canvas(lf_preview, bg="#2e3035", highlightthickness=0)
        self.canvas_preview.pack(fill=tk.BOTH, expand=True)
        self.canvas_preview.bind("<Configure>", lambda e: self.redraw_canvas())
        
    def on_preset_selected(self, event):
        key = self.combo_preset.get()
        if key in PRESETS:
            main_t, sub_t = PRESETS[key]
            self.txt_main.delete(0, tk.END)
            self.txt_main.insert(0, main_t)
            self.txt_sub.delete(0, tk.END)
            self.txt_sub.insert(0, sub_t)
            self.update_preview()
            
    def choose_color(self):
        color = colorchooser.askcolor(color=self.btn_color.cget("bg"), title="选择水印颜色")
        if color[0]:
            rgb = tuple(int(c) for c in color[0])
            hex_c = color[1]
            self.set_color(rgb, hex_c)
            
    def set_color(self, rgb, hex_c):
        self.watermark_color_rgb = rgb
        self.btn_color.configure(bg=hex_c)
        self.update_preview()
        
    def open_image(self):
        path = filedialog.askopenfilename(
            title="选择要添加水印的证件图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"), ("所有文件", "*.*")]
        )
        if path:
            self.load_image(path)
            
    def load_image(self, path):
        try:
            self.current_img = Image.open(path).convert("RGBA")
            self.current_filepath = path
            w, h = self.current_img.size
            self.lbl_file_info.config(text=f"已加载: {os.path.basename(path)} ({w}×{h} 像素)")
            self.update_preview()
        except Exception as e:
            messagebox.showerror("打开错误", f"无法打开图片:\n{e}")
            
    def apply_watermark(self, base_img):
        w, h = base_img.size
        diag = int(math.hypot(w, h)) + 800
        
        main_text = self.txt_main.get().strip()
        sub_text = self.txt_sub.get().strip()
        mode = self.var_mode.get()
        opacity_val = int(self.slider_opacity.get())
        self.lbl_opacity.config(text=f"{opacity_val}%")
        alpha = int(255 * (opacity_val / 100.0))
        color_rgba = self.watermark_color_rgb + (alpha,)
        
        scale = float(self.slider_fontsize.get())
        base_size = max(w, h)
        angle = float(self.slider_angle.get())
        
        wm_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        
        if mode == "tile":
            f_main_size = max(16, int(base_size * 0.024 * scale))
            f_sub_size = max(12, int(base_size * 0.015 * scale))
            font_main = ImageFont.truetype(FONT_BOLD, f_main_size)
            font_sub = ImageFont.truetype(FONT_REG, f_sub_size)
            
            tile_canvas = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
            d_tile = ImageDraw.Draw(tile_canvas)
            
            # 精确测量主副文字的实际像素宽度与高度，彻底防止横向碰撞重叠
            bbox_m = d_tile.textbbox((0, 0), main_text, font=font_main)
            w_m = bbox_m[2] - bbox_m[0]
            h_m = bbox_m[3] - bbox_m[1]
            
            w_s, h_s = 0, 0
            if sub_text:
                bbox_s = d_tile.textbbox((0, 0), sub_text, font=font_sub)
                w_s = bbox_s[2] - bbox_s[0]
                h_s = bbox_s[3] - bbox_s[1]
                
            text_block_w = max(w_m, w_s)
            text_block_h = h_m + (h_s + int(f_main_size * 0.45) if sub_text else 0)
            
            # 间距与疏密动态调节
            density_ratio = float(self.slider_density.get()) / 240.0
            gap_x = max(60, int(base_size * 0.08 * density_ratio))
            gap_y = max(40, int(base_size * 0.085 * density_ratio))
            
            step_x = text_block_w + gap_x
            step_y = text_block_h + gap_y
            
            for row, y in enumerate(range(0, diag, step_y)):
                x_off = (row % 2) * (step_x // 2)
                for x in range(-step_x, diag + step_x, step_x):
                    cx = x + x_off
                    d_tile.text((cx, y), main_text, fill=color_rgba, font=font_main, anchor="mm")
                    if sub_text:
                        d_tile.text((cx, y + int(f_main_size * 1.25)), sub_text, fill=color_rgba, font=font_sub, anchor="mm")
                        
            rot_tile = tile_canvas.rotate(angle, resample=Image.Resampling.BICUBIC)
            cx, cy = diag // 2, diag // 2
            left, top = cx - w // 2, cy - h // 2
            wm_layer = rot_tile.crop((left, top, left + w, top + h))
            
        elif mode == "banner":
            f_main_size = max(24, int(base_size * 0.038 * scale))
            f_sub_size = max(16, int(base_size * 0.020 * scale))
            font_main = ImageFont.truetype(FONT_BOLD, f_main_size)
            font_sub = ImageFont.truetype(FONT_BOLD, f_sub_size)
            
            bw = int(w * 0.96)
            bh = int(f_main_size * 2.8 + (f_sub_size * 1.8 if sub_text else 0))
            ribbon = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
            d_rib = ImageDraw.Draw(ribbon)
            
            # translucent box with outline
            box_bg = self.watermark_color_rgb + (max(10, int(alpha * 0.25)),)
            box_border = self.watermark_color_rgb + (min(255, int(alpha * 1.3)),)
            d_rib.rounded_rectangle([10, 10, bw-10, bh-10], radius=16, fill=box_bg, outline=box_border, width=max(2, int(w*0.0025)))
            
            cy_m = bh // 2 - (int(f_sub_size * 0.9) if sub_text else 0)
            d_rib.text((bw // 2, cy_m), main_text, fill=color_rgba, font=font_main, anchor="mm")
            if sub_text:
                d_rib.text((bw // 2, cy_m + int(f_main_size * 1.15)), sub_text, fill=color_rgba, font=font_sub, anchor="mm")
                
            rot_c = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
            rot_c.paste(ribbon, ((diag - bw)//2, (diag - bh)//2))
            rot_rib = rot_c.rotate(angle, resample=Image.Resampling.BICUBIC)
            cx, cy = diag // 2, diag // 2
            left, top = cx - w // 2, cy - h // 2
            wm_layer = rot_rib.crop((left, top, left + w, top + h))
            
        elif mode == "stamp":
            sw = int(w * 0.45 * scale)
            sh = int(sw * 0.52)
            sx = w - sw - int(w * 0.05)
            sy = h - sh - int(h * 0.05)
            
            d_st = ImageDraw.Draw(wm_layer)
            st_col = color_rgba
            st_bg = self.watermark_color_rgb + (max(15, int(alpha * 0.2)),)
            
            d_st.rounded_rectangle([sx, sy, sx+sw, sy+sh], radius=18, outline=st_col, width=max(3, int(sw*0.015)), fill=st_bg)
            d_st.rounded_rectangle([sx+8, sy+8, sx+sw-8, sy+sh-8], radius=12, outline=st_col, width=max(1, int(sw*0.006)))
            
            f_h = max(14, int(sh * 0.16))
            f_b = max(11, int(sh * 0.12))
            font_sh = ImageFont.truetype(FONT_BOLD, f_h)
            font_sb = ImageFont.truetype(FONT_REG, f_b)
            
            cx = sx + sw // 2
            d_st.text((cx, sy + int(sh * 0.22)), f"★ {main_text} ★", fill=st_col, font=font_sh, anchor="mm")
            d_st.line([sx + 20, sy + int(sh * 0.38), sx + sw - 20, sy + int(sh * 0.38)], fill=st_col, width=2)
            d_st.text((cx, sy + int(sh * 0.58)), sub_text or "仅供指定业务使用 · 再次复印无效", fill=st_col, font=font_sb, anchor="mm")
            d_st.text((cx, sy + int(sh * 0.78)), "【 严禁用于其他任何用途 · 违者必究 】", fill=st_col, font=font_sb, anchor="mm")
            
        # Composite
        return Image.alpha_composite(base_img, wm_layer)
        
    def update_preview(self):
        if self.current_img is None:
            # Create a mock certificate canvas if no image loaded
            mock = Image.new("RGBA", (1920, 1280), (248, 250, 252, 255))
            d = ImageDraw.Draw(mock)
            d.rectangle([40, 40, 1880, 1240], outline=(200, 210, 225, 255), width=4)
            d.rectangle([55, 55, 1865, 1225], outline=(225, 230, 240, 255), width=2)
            f_tip1 = ImageFont.truetype(FONT_BOLD, 54)
            f_tip2 = ImageFont.truetype(FONT_REG, 32)
            d.text((960, 580), "【请先导入您的证书或照片】", fill=(170, 180, 195, 255), font=f_tip1, anchor="mm")
            d.text((960, 660), "点击上方【打开图片】按钮，支持 JPG/PNG/扫描件", fill=(185, 195, 205, 255), font=f_tip2, anchor="mm")
            target = mock
        else:
            target = self.current_img
            
        self.watermarked_img = self.apply_watermark(target)
        self.redraw_canvas()
        
    def redraw_canvas(self):
        if self.watermarked_img is None:
            return
            
        cw = self.canvas_preview.winfo_width()
        ch = self.canvas_preview.winfo_height()
        if cw < 50 or ch < 50:
            return
            
        iw, ih = self.watermarked_img.size
        ratio = min(cw / iw, ch / ih)
        nw, nh = max(1, int(iw * ratio)), max(1, int(ih * ratio))
        
        # Fast thumbnail
        thumb = self.watermarked_img.resize((nw, nh), resample=Image.Resampling.BILINEAR)
        self.tk_photo = ImageTk.PhotoImage(thumb)
        
        self.canvas_preview.delete("all")
        px = (cw - nw) // 2
        py = (ch - nh) // 2
        self.canvas_preview.create_image(px, py, anchor=tk.NW, image=self.tk_photo)
        
    def save_image(self):
        if self.current_img is None:
            messagebox.showwarning("提示", "请先导入要添加水印的图片！")
            return
            
        default_name = "水印防盗_" + os.path.basename(self.current_filepath)
        save_path = filedialog.asksaveasfilename(
            title="保存添加水印后的图片",
            initialfile=default_name,
            defaultextension=".jpg",
            filetypes=[("JPEG图片 (*.jpg)", "*.jpg"), ("PNG高清图片 (*.png)", "*.png"), ("PDF文档 (*.pdf)", "*.pdf")]
        )
        if not save_path:
            return
            
        try:
            # Generate high-res original
            final_img = self.apply_watermark(self.current_img)
            
            ext = os.path.splitext(save_path)[1].lower()
            if ext in [".jpg", ".jpeg"]:
                final_rgb = final_img.convert("RGB")
                final_rgb.save(save_path, quality=95)
            elif ext == ".pdf":
                final_rgb = final_img.convert("RGB")
                final_rgb.save(save_path, "PDF", resolution=150.0)
            else:
                final_img.save(save_path)
                
            messagebox.showinfo("保存成功", f"文件已成功导出至：\n{save_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"导出文件时发生错误:\n{e}")
            
    def batch_process(self):
        in_dir = filedialog.askdirectory(title="选择包含待加水印图片的文件夹")
        if not in_dir:
            return
            
        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
        files = [os.path.join(in_dir, f) for f in os.listdir(in_dir) if os.path.splitext(f)[1].lower() in valid_exts]
        
        if not files:
            messagebox.showwarning("提示", "该文件夹内没有找到有效的图片文件！")
            return
            
        out_dir = os.path.join(in_dir, "水印已处理")
        os.makedirs(out_dir, exist_ok=True)
        
        count = 0
        for f in files:
            try:
                base = Image.open(f).convert("RGBA")
                res = self.apply_watermark(base)
                base_name = os.path.splitext(os.path.basename(f))[0]
                out_path = os.path.join(out_dir, f"{base_name}_防盗水印.jpg")
                res.convert("RGB").save(out_path, quality=95)
                count += 1
            except Exception as e:
                print(f"Failed processing {f}: {e}")
                
        messagebox.showinfo("批量处理完成", f"已成功处理 {count} 张图片！\n保存在：\n{out_dir}")

def main():
    root = tk.Tk()
    app = WatermarkApp(root)
    app.update_preview()
    root.mainloop()

if __name__ == "__main__":
    main()
