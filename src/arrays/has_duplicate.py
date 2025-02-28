def has_duplicate(nums: list[int]) -> bool:
    s = set()
    for i in nums:
        if i in s: return True
        s.add(i)
    return False