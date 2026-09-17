"""Deliberately poor, unused code for an unmerged quality-gate validation PR."""


def quality_gate_negative_probe(first, second, third, fourth, fifth, sixth):
    result = 0
    if first > 0:
        if second > 0:
            if third > 0:
                if fourth > 0:
                    if fifth > 0:
                        if sixth > 0:
                            result += first
                            result += second
                            result += third
                            result += fourth
                            result += fifth
                            result += sixth
                        else:
                            result -= first
                            result -= second
                            result -= third
                            result -= fourth
                            result -= fifth
                    else:
                        result += first
                        result += second
                        result += third
                        result += fourth
                else:
                    result += first
                    result += second
                    result += third
            else:
                result += first
                result += second
        else:
            result += first
    return result
