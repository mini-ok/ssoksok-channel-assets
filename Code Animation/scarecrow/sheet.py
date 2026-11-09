import sys
from PIL import Image
fs=sys.argv[2:]; out=sys.argv[1]
w,h=960,540; cols=2
rows=(len(fs)+1)//2
sh=Image.new('RGB',(w*cols,h*rows))
for i,f in enumerate(fs):
    sh.paste(Image.open(f).convert('RGB').resize((w,h),Image.LANCZOS),((i%cols)*w,(i//cols)*h))
sh.save(out)
