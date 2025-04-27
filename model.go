package chaincode

/*
定义用户结构体
用户ID
用户类型
实名认证信息哈希,包括用户注册的姓名、身份证号、手机号、注册平台同意协议签名的哈希
 原材料列表
*/
type User struct {
	UserID       string   `json:"userID"`
	UserType     string   `json:"userType"`
	RealInfoHash string   `json:"realInfoHash"`
	FruitList    []*Fruit `json:"fruitList"`
}

/*
定义原材料结构体
溯源码
原材料供应方输入
中央厨房输入
运输司机输入
经销商输入
*/
type Fruit struct {
	Traceability_code string        `json:"traceability_code"`
	Farmer_input      Farmer_input  `json:"farmer_input"`
	Factory_input     Factory_input `json:"factory_input"`
	Driver_input      Driver_input  `json:"driver_input"`
	Shop_input        Shop_input    `json:"shop_input"`
}

// HistoryQueryResult structure used for handling result of history query
type HistoryQueryResult struct {
	Record    *Fruit `json:"record"`
	TxId      string `json:"txId"`
	Timestamp string `json:"timestamp"`
	IsDelete  bool   `json:"isDelete"`
}

/*
原材料供应方
原材料的溯源码，一物一码，主打高端市场（自动生成）
原材料名称
产地
内容清单
供应时间
供应方名称
*/
type Farmer_input struct {
	Fa_fruitName   string `json:"fa_fruitName"`
	Fa_origin      string `json:"fa_origin"`
	Fa_plantTime   string `json:"fa_plantTime"`
	Fa_pickingTime string `json:"fa_pickingTime"`
	Fa_farmerName  string `json:"fa_farmerName"`
	Fa_imgHash  string `json:"fa_imgHash"`
	Fa_Txid        string `json:"fa_txid"`
	Fa_Timestamp   string `json:"fa_timestamp"`
}

/*
中央厨房
预制食品名称
生产批次
生产时间（可以防止黑心商家修改时间）
制作食谱
中央厨房名称地址及电话
*/
type Factory_input struct {
	Fac_productName     string `json:"fac_productName"`
	Fac_productionbatch string `json:"fac_productionbatch"`
	Fac_productionTime  string `json:"fac_productionTime"`
	Fac_factoryName     string `json:"fac_factoryName"`
	Fac_contactNumber   string `json:"fac_contactNumber"`
	Fac_imgHash  string `json:"fac_imgHash"`
	Fac_Txid            string `json:"fac_txid"`
	Fac_Timestamp       string `json:"fac_timestamp"`
}

/*
运输司机
姓名
年龄
电话
车牌号
运输记录
*/
type Driver_input struct {
	Dr_name      string `json:"dr_name"`
	Dr_age       string `json:"dr_age"`
	Dr_phone     string `json:"dr_phone"`
	Dr_carNumber string `json:"dr_carNumber"`
	Dr_transport string `json:"dr_transport"`
	Dr_imgHash  string `json:"dr_imgHash"`
	Dr_Txid      string `json:"dr_txid"`
	Dr_Timestamp string `json:"dr_timestamp"`
}

/*
经销商
入库时间
销售时间
经销商名称
经销商位置
经销商电话
*/
type Shop_input struct {
	Sh_storeTime   string `json:"sh_storeTime"`
	Sh_sellTime    string `json:"sh_sellTime"`
	Sh_shopName    string `json:"sh_shopName"`
	Sh_shopAddress string `json:"sh_shopAddress"`
	Sh_shopPhone   string `json:"sh_shopPhone"`
	Sh_imgHash  string `json:"sh_imgHash"`
	Sh_Txid        string `json:"sh_txid"`
	Sh_Timestamp   string `json:"sh_timestamp"`
}
