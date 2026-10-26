import pickle, sys, capstone
insns = pickle.load(open('insns.pkl','rb'))
byaddr = {a:(a,s,mn,op,bb) for a,s,mn,op,bb in insns}
data = open('../Etherlords_max/reference/Etherlords.exe','rb').read()
BASE=0x400000; TEXT_FILE=0x1000; TEXT_VA=0x401000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va, n=150):
    if va in byaddr:
        out=[]; a=va
        for i in range(n):
            t=byaddr.get(a)
            if not t: break
            a2,s,mn,op,bb=t
            out.append(f'{a2:#010x}  {bb.hex(" "):<26} {mn} {op}')
            a=a2+s
            if mn=='ret': break
        return '\n'.join(out)
    off = TEXT_FILE + (va-TEXT_VA)
    code = data[off:off+4*n]
    out=[]
    for i in md.disasm(code, va):
        out.append(f'{i.address:#010x}  {i.bytes.hex(" "):<26} {i.mnemonic} {i.op_str}')
        if i.mnemonic=='ret': break
    return '\n'.join(out)
if __name__=='__main__':
    va=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 150
    print(dis(va,n))
