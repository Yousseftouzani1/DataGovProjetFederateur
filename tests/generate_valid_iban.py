def generate_iban(base_str):
    def conv(c):
        return str(ord(c) - ord('A') + 10) if c.isalpha() else c
    
    # 1. Convert rib to digits
    rib_digits = "".join(conv(c) for c in base_str)
    
    # 2. Add MA00 (MA=2210) to the end: rib + 2210 + 00
    # In IBAN calculation, we shift MAxx to end and replace letters with digits.
    # To find xx, we use MA00 = 221000
    rearranged_digits = rib_digits + "221000"
    
    # 3. remainder = rearranged_digits % 97
    remainder = int(rearranged_digits) % 97
    
    # 4. check = 98 - remainder
    check = 98 - remainder
    
    return f"MA{check:02d}{base_str}"

if __name__ == "__main__":
    rib_alpha = "PXAF5XLFR848NM2UHJMKPA0C"
    print(f"Alpha: {generate_iban(rib_alpha)}")
    
    rib_num = "123456789012345678901234"
    print(f"Numeric: {generate_iban(rib_num)}")
