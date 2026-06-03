def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)


def quicksort_inplace(arr, lo=0, hi=None):
    if hi is None:
        hi = len(arr) - 1
    if lo >= hi:
        return

    pivot = arr[(lo + hi) // 2]
    i, j = lo, hi
    while i <= j:
        while arr[i] < pivot:
            i += 1
        while arr[j] > pivot:
            j -= 1
        if i <= j:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
            j -= 1

    quicksort_inplace(arr, lo, j)
    quicksort_inplace(arr, i, hi)


if __name__ == "__main__":
    data = [3, 6, 8, 10, 1, 2, 1, 7, 5, 9, 4]

    copy1 = data[:]
    print("functional:", quicksort(copy1))

    copy2 = data[:]
    quicksort_inplace(copy2)
    print("in-place:  ", copy2)
