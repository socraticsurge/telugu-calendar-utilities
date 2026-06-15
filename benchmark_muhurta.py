import timeit
from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID

def test_membership_list():
    setup_code = """
from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
yoga_name = 'Vyatipata'
"""
    stmt = "yoga_name in NITYA_HARD_AVOID"
    times = timeit.repeat(stmt, setup=setup_code, number=10000000, repeat=5)
    print(f"List/Tuple/Set: {min(times):.4f} seconds")

if __name__ == "__main__":
    test_membership_list()
