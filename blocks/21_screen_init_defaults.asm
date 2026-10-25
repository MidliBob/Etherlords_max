; 21_screen_init_defaults
; file 0x19bc9e..0x19bd28  va 0x59bc9e..0x59bd28
; CScreenManager::Init: set_rect(0,0,800,600) для subscreens +0xb4/+0xb8/+0xc0 и [0x82bc58]; загрузка Controls.reg (0x58be10) и CutParts.reg (0x58ca90); ApplyShifts (0x58ca30).
  0x0059bc9e  55                push ebp
  0x0059bc9f  e8 ec 39 ff ff    call 0x58f690
  0x0059bca4  8b 8e b4 00 00 00  mov ecx, dword ptr [esi + 0xb4]
  0x0059bcaa  55                push ebp
  0x0059bcab  e8 e0 39 ff ff    call 0x58f690
  0x0059bcb0  8b 8e b8 00 00 00  mov ecx, dword ptr [esi + 0xb8]
  0x0059bcb6  55                push ebp
  0x0059bcb7  e8 d4 39 ff ff    call 0x58f690
  0x0059bcbc  8b 8e c0 00 00 00  mov ecx, dword ptr [esi + 0xc0]
  0x0059bcc2  55                push ebp
  0x0059bcc3  e8 c8 39 ff ff    call 0x58f690
  0x0059bcc8  8b 0d 58 bc 82 00  mov ecx, dword ptr [0x82bc58]
  0x0059bcce  55                push ebp
  0x0059bccf  e8 bc 39 ff ff    call 0x58f690
  0x0059bcd4  8b 0d 68 b9 82 00  mov ecx, dword ptr [0x82b968]
  0x0059bcda  e8 31 01 ff ff    call 0x58be10
  0x0059bcdf  8b 0d 68 b9 82 00  mov ecx, dword ptr [0x82b968]
  0x0059bce5  e8 56 16 ff ff    call 0x58d340
  0x0059bcea  8b 15 60 9f 82 00  mov edx, dword ptr [0x829f60]
  0x0059bcf0  8b 46 4c          mov eax, dword ptr [esi + 0x4c]
  0x0059bcf3  8b 88 e0 01 00 00  mov ecx, dword ptr [eax + 0x1e0]
  0x0059bcf9  52                push edx
  0x0059bcfa  e8 01 dd fa ff    call 0x549a00
  0x0059bcff  8b 0d 68 b9 82 00  mov ecx, dword ptr [0x82b968]
  0x0059bd05  e8 26 0d ff ff    call 0x58ca30
  0x0059bd0a  68 58 02 00 00    push 0x258
  0x0059bd0f  68 20 03 00 00    push 0x320
  0x0059bd14  6a 00             push 0
  0x0059bd16  6a 00             push 0
  0x0059bd18  55                push ebp
  0x0059bd19  ff 15 28 64 75 00  call dword ptr [0x756428]
  0x0059bd1f  8b 4e 08          mov ecx, dword ptr [esi + 8]
  0x0059bd22  55                push ebp
  0x0059bd23  e8 68 39 ff ff    call 0x58f690
