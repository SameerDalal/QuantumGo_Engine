def case_a_19x19():
    return -179.750

def case_b_19x19():
    return -159.777

def case_c_19x19():
    return -139.805

def case_d_19x19():
    return -119.833

def case_e_19x19():  
    return -99.861

def case_f_19x19():
    return -79.888

def case_g_19x19():   
    return -59.916

def case_h_19x19():
    return -39.944

def case_i_19x19():
    return -19.972

def case_j_19x19():
    return 0.000

def case_k_19x19():
    return 19.972

def case_l_19x19():
    return 39.944

def case_m_19x19():
    return 59.916

def case_n_19x19():
    return 79.888

def case_o_19x19():
    return 99.861

def case_p_19x19():
    return 119.833

def case_q_19x19():
    return 139.805

def case_r_19x19():
    return 159.777

def case_s_19x19():
    return 179.750

def default_case_19x19():
    return None


switch_19x19 = {

    1: case_a_19x19,
    2: case_b_19x19,
    3: case_c_19x19,
    4: case_d_19x19,
    5: case_e_19x19,
    6: case_f_19x19,
    7: case_g_19x19,
    8: case_h_19x19,
    9: case_i_19x19,
    10: case_j_19x19,
    11: case_k_19x19,
    12: case_l_19x19,
    13: case_m_19x19,
    14: case_n_19x19,
    15: case_o_19x19,
    16: case_p_19x19,
    17: case_q_19x19,
    18: case_r_19x19,
    19: case_s_19x19

}

def get_offset_19x19(action):
    return (
        
        switch_19x19.get(action[0] + 1, default_case_19x19)(),
        switch_19x19.get(action[1] + 1, default_case_19x19)()
        
        )


def case_a_9x9():
    return -159.999

def case_b_9x9():
    return -119.999

def case_c_9x9():
    return -79.999

def case_d_9x9():
    return -39.999

def case_e_9x9():
    return 0

def case_f_9x9():
    return 39.999

def case_g_9x9():
    return 79.999

def case_h_9x9():
    return 119.999

def case_i_9x9():
    return 159.999

def default_case_9x9():
    return None

switch_9x9 = {

    1: case_a_9x9,
    2: case_b_9x9,
    3: case_c_9x9,
    4: case_d_9x9,
    5: case_e_9x9,
    6: case_f_9x9,
    7: case_g_9x9,
    8: case_h_9x9,
    9: case_i_9x9,

}

def get_offset_9x9(action):


    return (
        
        switch_9x9.get(action[0] + 1, default_case_9x9)(),
        switch_9x9.get(action[1] + 1, default_case_9x9)()
        
    )


def case_a_5x5():
    return -159.999

def case_b_5x5():
    return -80.000

def case_c_5x5():
    return 0

def case_d_5x5():
    return 80.000

def case_e_5x5():
    return 159.999

def default_case_5x5():
    return None


switch_5x5 = {

    1: case_a_5x5,
    2: case_b_5x5,
    3: case_c_5x5,
    4: case_d_5x5,
    5: case_e_5x5,
}

def get_offset_5x5(action):

    return (
        
        switch_5x5.get(action[0] + 1, default_case_5x5)(),
        switch_5x5.get(action[1] + 1, default_case_5x5)()
        
    )
