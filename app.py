# --- 6. LIỆT KÊ 10 SUBID ĐÓNG GÓP NHIỀU NHẤT ---
        st.subheader("6. Top 10 SubID đóng góp đơn nhiều nhất")
        
        # Danh sách các cột Sub_id cần gộp
        sub_id_cols = ['Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']
        
        # Tạo một danh sách tạm để chứa dữ liệu gộp
        sub_data_list = []
        
        for col in sub_id_cols:
            if col in df_filtered.columns:
                # Lấy các dòng có dữ liệu Sub_id (không bị trống)
                temp_df = df_filtered[df_filtered[col].notna()][[col, 'Tổng hoa hồng đơn hàng(₫)']]
                temp_df.columns = ['Subid_Name', 'HoaHồng']
                sub_data_list.append(temp_df)
        
        if sub_data_list:
            # Gộp tất cả các sub_id từ 5 cột thành 1 bảng duy nhất
            all_sub_data = pd.concat(sub_data_list)
            
            # Nhóm và tính toán
            top_sub = all_sub_data.groupby('Subid_Name').agg(
                Số_lượng_đơn=('Subid_Name', 'count'),
                Số_tiền_hoa_hồng=('HoaHồng', 'sum')
            ).reset_index()
            
            # Sắp xếp theo số lượng đơn giảm dần như yêu cầu
            top_sub = top_sub.sort_values('Số_lượng_đơn', ascending=False).head(10)
            
            # Định dạng hiển thị
            top_sub['Số_tiền_hoa_hồng'] = top_sub['Số_tiền_hoa_hồng'].map('{:,.0f} ₫'.format)
            
            st.table(top_sub) # Dùng bảng tĩnh để nhìn rõ ràng hơn
        else:
            st.warning("Không tìm thấy dữ liệu trong các cột Sub_id.")
